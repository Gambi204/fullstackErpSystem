import random
from datetime import datetime

import phonenumbers
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from pip._internal.utils import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from simplejwt import jwt

from .models import Company, User
from .serializers import CompanySerializer, UserSerializer, UserDetailsSerializer
from django.core.exceptions import ValidationError
from phonenumbers import parse, format_number, region_code_for_number
from pycountry import countries
import jwt
import datetime
from .models import UserOTP


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance = None

    @action(detail=False, methods=['post'])
    def register(self, request):
        try:
            # 1. Field Validation with Custom Serializer
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # 2. Duplicate Check
            duplicate_exists = Company.objects.filter(email=request.data['email']).exists()
            if duplicate_exists and request.data.get('is_approved', False):
                return Response({'error': 'Company already approved.'}, status=status.HTTP_400_BAD_REQUEST)
            elif duplicate_exists:
                # Allow multiple registrations for non-approved companies
                pass

            # 3. Extract Country Code and Name from Phone Number (if applicable)
            phone_number = request.data.get('phone_number')
            if phone_number:
                try:
                    parsed_number = parse(phone_number)
                    self.instance.country_code = f"+{parsed_number.country_code}"
                    self.instance.number = format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)

                    # Get country name from country code
                    country_code = region_code_for_number(parsed_number)
                    country = countries.get(alpha_2=country_code)
                    if country:
                        self.instance.country = country.name
                except phonenumbers.phonenumberutil.NumberParseException as e:
                    raise ValidationError(f"Invalid phone number: {e}")

            # 4. Save with Conditional Approval and Email Notification
            self.instance = serializer.save(is_approved=False)
            send_mail(
                'Registration Request Received',
                'Your registration request has been received and is awaiting approval.',
                'from@example.com',
                [self.instance.email],
                fail_silently=False,
            )

            return Response({'status': 'pending approval'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        try:
            company = self.get_object()
            if company.is_approved:
                return Response({"message": "Company already approved"}, status=status.HTTP_400_BAD_REQUEST)

            # Create an admin user for the approved company
            admin_user = User.objects.create(
                username=f"{company.email.split('@')[0]}-{random.randint(1000, 9999)}",
                email=company.email,
                company=company,
                password=f"{random.randint(100000, 999999)}",
                is_manager=True,
                is_superuser=False,
                is_staff=True
            )
            admin_user.set_password('jikoTrack@2024')
            admin_user.save()

            send_mail(
                'Registration Approved',
                f"""Your registration has been approved. Here are your admin credentials:\n\nUsername: {admin_user.username}\nPassword: jikoTrack@2024""",
                'from@example.com',
                [company.email],
                fail_silently=False,
            )

            # Update the company's approval status after email is sent
            company.is_approved = True
            company.save()

            return Response({'status': 'approved'})
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def companiesList(self, request):
        companies = Company.objects.filter(is_approved=True)
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    methods=['get']
    def getAllCompanies(self, request):
        try:
            companies = Company.objects.all()
            company_list = []

            for company in companies:
                company_details = {
                    'id': company.id,
                    'name': company.companyName,
                    'email': company.email,
                    'country': company.country,
                    'city': company.city,
                    'companySize': company.companySize,
                    'primaryInterest': company.primaryInterest,
                    'is_approved': company.is_approved,
                }
                company_list.append(company_details)

            return Response(company_list, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'])
    def login(self, request):
        try:
            username = request.data.get('username').lower()
            password = request.data.get('password')

            user = authenticate(username=username, password=password)
            if not user:
                return Response({"message": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
                'iat': datetime.datetime.utcnow(),
                'sub': user.id
            }

            token = jwt.encode(payload, 'secret', algorithm='HS256')
            company = Company.objects.get(id=user.company_id)
            user_details = {
                'token': token,
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'company_name': company.companyName,
                'is_manager': user.is_manager,
                'is_accounting_manager': user.is_accounting_manager,
                'is_inventory_manager': user.is_inventory_manager,
                'is_purchase_manager': user.is_purchase_manager,
            }

            response = Response()
            response.set_cookie(key='jwt', value=token, httponly=True)
            response.data = {
                'jwt': token,
                'user_details': user_details
            }

            return response

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def createUser(self, request):
        try:
            # Convert roles from word form to the form understood by the serializer
            role_mapping = {
                'Manager': 'is_manager',
                'Admin': 'is_superuser',
                'Accounting Manager': 'is_accounting_manager',
                'Inventory Manager': 'is_inventory_manager',
                'Purchase Manager': 'is_purchase_manager',
                'User': None  # No specific role for 'User'
            }

            role = request.data.get('role')
            if role:
                role_field = role_mapping.get(role)
                if role_field is not None:
                    request.data[role_field] = True

            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()

                send_mail(
                    'Welcome to JikoTrack!',
                    f"""
                        Thank you for creating an account with our app!

                        You can now log in using your username: {user.username}

                        For security reasons, your password is not included in this email.
                        Please visit the login page to set your password.

                        We hope you enjoy using our app!

                        Sincerely,
                        JikoTrack Team
                        """,
                    'from@example.com',
                    [user.email],
                    fail_silently=False,
                )

                return Response({'status': 'user created'}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def getUsers(self, request):
        try:
            # Get the JWT token from the cookies
            token = request.COOKIES.get('jwt')

            if not token:
                return Response({"message": "Authentication token not provided"}, status=status.HTTP_401_UNAUTHORIZED)

            # Decode the JWT token
            try:
                payload = jwt.decode(token, 'secret', algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return Response({"message": "Authentication token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"message": "Invalid authentication token"}, status=status.HTTP_401_UNAUTHORIZED)

            # Get the user ID from the payload
            user_id = payload['sub']

            # Retrieve the user
            user = User.objects.get(id=user_id)

            # Check if the user exists
            if not user:
                return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Retrieve the company details of the user
            company = Company.objects.get(id=user.company_id)

            # User details to return
            user_details = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'company_name': company.companyName,
                'is_manager': user.is_manager,
                'is_accounting_manager': user.is_accounting_manager,
                'is_inventory_manager': user.is_inventory_manager,
                'is_purchase_manager': user.is_purchase_manager,
            }

            return Response({'user_details': user_details}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def getUserById(self, request, user_id):
        try:
            token = request.COOKIES.get('jwt')

            if not token:
                return Response({"message": "Authentication token is missing"}, status=400)

            try:
                payload = jwt.decode(token, 'secret', algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return Response({"message": "Token has expired"}, status=401)
            except jwt.InvalidTokenError:
                return Response({"message": "Invalid token"}, status=401)

            user = get_object_or_404(User, id=user_id)
            company = Company.objects.get(id=user.company_id)

            user_details = {
                'username': user.username,
                'email': user.email,
                'role': 'Manager' if user.is_manager else
                'Accounting Manager' if user.is_accounting_manager else
                'Inventory Manager' if user.is_inventory_manager else
                'Purchase Manager' if user.is_purchase_manager else
                'User',
                'company_name': company.name
            }

            return Response(user_details, status=200)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def forgotPassword(self, request):
        try:
            username_or_email = request.data.get('username') or request.data.get('email')
            if not username_or_email:
                raise ValidationError('Username or email is required')

            user = User.objects.filter(Q(username=username_or_email) | Q(email=username_or_email)).first()
            if not user:
                return Response({'status': 'user not found'}, status=status.HTTP_404_NOT_FOUND)

            # Get or create the OTP record for the user
            user_otp, created = UserOTP.objects.get_or_create(user=user)

            # Generate and save the OTP
            user_otp.generate_otp()

            # Send email with OTP
            send_mail(
                'Password Reset Request',
                f'Your one-time password (OTP) to reset your password is: {user_otp.otp}',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )

            return Response({'status': 'otp sent'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def forgotPasswordOtpVerification(self, request):
        try:
            otp = request.data.get('otp')
            if not otp:
                return Response({'message': 'OTP is required'}, status=status.HTTP_400_BAD_REQUEST)

            user_otp = UserOTP.objects.filter(otp=otp).first()

            if not user_otp:
                return Response({'message': 'User not found or OTP is incorrect'}, status=status.HTTP_404_NOT_FOUND)

            # Check if OTP has expired (assuming OTP is valid for 10 minutes)
            otp_age = timezone.now() - user_otp.created_at
            if otp_age.seconds > 6000:
                return Response({'message': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

            user = user_otp.user
            user.is_active = True
            user.save()

            # Clean up the OTP after successful verification
            user_otp.otp = None
            user_otp.save()

            return Response({'message': 'Account verified successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def newPassword(self, request):
        try:
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            if not new_password or not confirm_password:
                raise ValidationError('Both new password and confirm password are required.')

            if new_password != confirm_password:
                raise ValidationError('Passwords do not match.')

            # Locate user by username or email
            username_or_email = request.data.get('username') or request.data.get('email')
            if not username_or_email:
                raise ValidationError('Username or email is required.')

            user = User.objects.filter(Q(username=username_or_email) | Q(email=username_or_email)).first()
            if not user:
                return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Update the user's password
            user.password = make_password(new_password)
            user.save()

            return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        except ValidationError as ve:
            return Response({'message': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            logout(request)
            return Response({'status': 'logged out'})
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def getAllUsers(self, request):
        try:
            users = User.objects.all()
            user_list = []

            for user in users:
                company = get_object_or_404(Company, id=user.company_id)
                user_details = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': 'Manager' if user.is_manager else
                    'Accounting Manager' if user.is_accounting_manager else
                    'Inventory Manager' if user.is_inventory_manager else
                    'Purchase Manager' if user.is_purchase_manager else
                    'User',
                    'company': company.name,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined
                }
                user_list.append(user_details)

            return Response(user_list, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'])
    def updateUser(self, request, user_id):
        try:
            user = get_object_or_404(User, id=user_id)
            data = request.data
            allowed_fields = ['username', 'email', 'role']
            updated_data = {field: data[field] for field in allowed_fields if field in data}

            serializer = UserSerializer(user, data=updated_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'])
    def delete(self, request, user_id):
        user = get_object_or_404(User, user_id)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def roles(self, request):
        roles = [
            {'label': 'Manager', 'value': 'Manager'},
            {'label': 'Admin', 'value': 'Admin'},
            {'label': 'User', 'value': 'User'},
            {'label': 'Accounting Manager', 'value': 'Accounting Manager'},
            {'label': 'Inventory Manager', 'value': 'Inventory Manager'},
            {'label': 'Purchase Manager', 'value': 'Purchase Manager'}
        ]
        return Response(roles, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def authChecker(self, request):
        try:
            user = request.user
            user_data = {
                "name": user.username,
                "email": user.email,
                "role": user.roles
            }
            return Response({"isAuthenticated": True, "user": user_data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"Error; {str(e)}"})
