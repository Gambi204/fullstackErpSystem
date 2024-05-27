<template>
    <div class="fixed inset-0 flex items-center justify-center bg-gray-500 bg-opacity-75">
        <form @submit.prevent="submit" class="w-full max-w-lg px-8">
            <div class="bg-white px-10 py-8 rounded-xl w-screen shadow-md max-w-sm">
                <img class="h-14 mb-4 mx-auto" src="/public/logoTrack.drawio.png" alt="">
                <div class="space-y-4">
                    <h1 class="text-center text-2xl font-semibold text-gray-600">Login</h1>
                    <div>
                        <label for="username" class="block mb-1 text-gray-600 font-semibold">Username</label>
                        <input id="username" v-model="username" type="text"
                            class="bg-indigo-50 px-4 py-2 outline-none rounded-md w-full" />
                    </div>

                    <div>
                        <label for="password" class="block mb-1 text-gray-600 font-semibold">Password</label>
                        <input id="password" v-model="password" type="password"
                            class="bg-indigo-50 px-4 py-2 outline-none rounded-md w-full" />
                    </div>
                    <div class="flex items-center justify-between">
                        <div class="flex items-start">
                            <div class="flex items-center h-5">
                                <input id="remember" aria-describedby="remember" type="checkbox"
                                    class="w-4 h-4 border border-gray-300 rounded bg-yellow-500 focus:ring-3 focus:ring-yellow-500 dark:bg-gray-700 dark:border-gray-600 dark:focus:ring-yellow-500 dark:ring-offset-gray-800">
                            </div>
                            <div class="ml-3 text-sm">
                                <label for="remember" class="text-gray-500 dark:text-black">Remember me</label>
                            </div>
                        </div>
                        <nuxt-link to="/passwordReset"
                            class="text-sm font-medium text-primary-600 hover:underline dark:text-yellow-500">Forgot
                            password?</nuxt-link>
                    </div>
                </div>
                <button @click="submit"
                    class="mt-4 w-full bg-yellow-500 font-semibold py-2 rounded-md tracking-wide">Login</button>
                <div>
                    <p class="mt-5 text-sm font-light text-yellow-500 dark:text-black">
                        Don’t have an account yet? <nuxt-link to="/Signup/signup"
                            class="font-medium text-primary-600 hover:underline dark:text-yellow-500">Sign
                            up</nuxt-link>
                    </p>
                </div>
            </div>
        </form>
    </div>
</template>

<script>
export default {
  name: 'Login',
  data() {
    return {
      username: '',
      password: '',
      alertMessage: '',
    };
  },
  methods: {
    async submit() {
      try {
        const response = await fetch('http://127.0.0.1:8000/backend/users/login/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: this.username,
            password: this.password,
          }),
        });

        const userData = await response.json();

        if (response.ok) {
          // Extract JWT token from response
          const jwtToken = userData.jwt;
          
          // Set JWT token in cookies
          document.cookie = `jwt=${jwtToken}; path=/`;

          alert('Login was successful.');

          // Routing based on user role
          if (userData.user_details.is_manager) {
            this.$router.push('/home/manager');
          } else if (userData.user_details.is_accounting_manager) {
            this.$router.push('/accounting');
          } else if (userData.user_details.is_inventory_manager) {
            this.$router.push('/inventory');
          } else if (userData.user_details.is_purchase_manager) {
            this.$router.push('/purchase');
          } else {
            this.alertMessage = 'Invalid role';
          }
        } else {
          console.error("Error in getUser response:", userData);
          throw new Error(userData.message || 'Failed to get user details');
        }
      } catch (error) {
        console.error("An error occurred:", error);
        this.alertMessage = 'An error occurred: ' + error.message;
      }
    }
  }
}
</script>


<style scoped>
.bg-opacity-75 {
    background-color: rgba(0, 0, 0, 0.75);
}
</style>
