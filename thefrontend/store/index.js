import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    user: null,
  },
  mutations: {
    setUser(state, user) {
      state.user = user;
    },
    clearUser(state) {
      state.user = null;
    }
  },
  actions: {
    async fetchUser({ commit }) {
      try {
        const response = await fetch('http://127.0.0.1:8000/backend/users/getuser/', {
          method: "GET",
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const content = await response.json();
        commit('setUser', content.name);
        window.dispatchEvent(new CustomEvent('auth', { detail: true }));
      } catch (e) {
        commit('clearUser');
        window.dispatchEvent(new CustomEvent('auth', { detail: false }));
      }
    },
    async logout({ commit }) {
      try {
        await fetch('http://127.0.0.1:8000/backend/users/logout', {
          method: "POST",
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        });

        commit('clearUser');
      } catch (error) {
        console.error('Error during logout:', error);
      }
    }
  },
  getters: {
    isAuthenticated: state => !!state.user,
    user: state => state.user,
  }
});
