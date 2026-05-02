import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import authApi from '../services/authApi';

const AuthContext = createContext(null);

AuthProvider.propTypes = { children: PropTypes.node.isRequired };
export function AuthProvider({ children }) {
  const [user, setUser]           = useState(null);
  const [profile, setProfile]     = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [avatarTs, setAvatarTs]   = useState(Date.now());
  const booted                    = useRef(false);

  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    authApi
      .getCurrentUser()
      .then((data) => setUser(data.user))
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    setUser(data.user);
    setProfile(null);
    return data;
  }, []);

  const register = useCallback(async (name, email, password) => {
    const data = await authApi.register(name, email, password);
    setUser(data.user);
    setProfile(null);
    return data;
  }, []);

  const logout = useCallback(async () => {
    try { await authApi.logout(); } catch (_) {}
    setUser(null);
    setProfile(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    const data = await authApi.getProfile();
    setProfile(data.profile);
    return data;
  }, []);

  const bumpAvatarTs = useCallback(() => setAvatarTs(Date.now()), []);

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        isLoading,
        isAuthenticated: !!user,
        avatarTs,
        login,
        logout,
        register,
        refreshProfile,
        setProfile,
        bumpAvatarTs,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}
