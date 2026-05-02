import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Edit3, Globe, Building2, Clock, Calendar, Mail, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import ProtectedRoute from '../components/auth/ProtectedRoute';

function ProfileContent() {
  const { user, profile, refreshProfile, avatarTs } = useAuth();
  const [isLoading, setIsLoading] = useState(!profile);
  const [avatarImgError, setAvatarImgError] = useState(false);

  useEffect(() => {
    if (!profile) {
      refreshProfile().finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [profile, refreshProfile]);

  const displayName = profile?.display_name || user?.name || 'User';
  const joinDate = user?.created_at
    ? new Date(user.created_at * 1000 || user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
    : '';

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.07 } },
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.38, ease: [0.22, 1, 0.36, 1] } },
  };

  if (isLoading) {
    return (
      <div className="app-page">
        <div className="app-shell mx-auto max-w-3xl space-y-5">
          <div className="app-card app-card-strong p-8 text-center">
            <span className="app-skeleton mx-auto mb-5 block h-32 w-32 rounded-full" />
            <span className="app-skeleton mx-auto mb-2 block h-7 w-40" />
            <span className="app-skeleton mx-auto block h-4 w-24" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[0, 1].map((i) => <span key={i} className="app-skeleton block h-20 rounded-2xl" />)}
          </div>
        </div>
      </div>
    );
  }

  const detailItems = [
    { icon: Mail, label: 'Email', value: user?.email },
    { icon: User, label: 'Account name', value: user?.name },
    { icon: Building2, label: 'Company', value: profile?.company },
    { icon: Globe, label: 'Website', value: profile?.website, isLink: true },
  ].filter((d) => !!d.value);

  return (
    <div className="app-page">
      <div className="app-shell mx-auto max-w-3xl">
        <motion.div initial="hidden" animate="visible" variants={containerVariants}>
          <motion.div variants={itemVariants} className="app-card app-card-strong mb-6 p-8 text-center">
            <div className="relative mx-auto mb-5 h-28 w-28 sm:h-32 sm:w-32">
              {avatarImgError ? (
                <div className="h-full w-full rounded-full border-4 border-primary-100 shadow-medium bg-primary-50 dark:bg-primary-950/30 flex items-center justify-center">
                  <User className="h-12 w-12 text-primary-300 dark:text-primary-700" aria-hidden="true" />
                </div>
              ) : (
                <img
                  key={avatarTs}
                  src={`/api/v1/profile/me/avatar?t=${avatarTs}`}
                  alt={displayName}
                  className="h-full w-full rounded-full border-4 border-primary-100 object-cover shadow-medium"
                  onError={() => setAvatarImgError(true)}
                />
              )}
              <Link
                to="/profile/edit"
                className="absolute -bottom-1 -right-1 flex h-9 w-9 items-center justify-center rounded-full border-2 border-white bg-primary-600 text-white shadow-soft transition-colors hover:bg-primary-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
                aria-label="Edit profile picture"
              >
                <Edit3 className="h-4 w-4" aria-hidden="true" />
              </Link>
            </div>

            <h1 className="mb-1 text-2xl font-black tracking-tight text-slate-950 dark:text-slate-50 sm:text-3xl">{displayName}</h1>
            {profile?.headline && (
              <p className="mb-2 text-base font-semibold text-primary-700 dark:text-violet-400">{profile.headline}</p>
            )}
            <p className="text-sm text-slate-500 dark:text-slate-400">{user?.email}</p>

            <div className="mt-5 flex flex-wrap justify-center gap-2">
              {joinDate && (
                <span className="app-pill-muted flex items-center gap-1.5 text-xs">
                  <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
                  Joined {joinDate}
                </span>
              )}
              {profile?.timezone && (
                <span className="app-pill-muted flex items-center gap-1.5 text-xs">
                  <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                  {profile.timezone}
                </span>
              )}
            </div>

            <div className="mt-6">
              <Link to="/profile/edit" className="app-button-secondary app-button-compact inline-flex">
                <Edit3 className="h-4 w-4" aria-hidden="true" />
                Edit Profile
              </Link>
            </div>
          </motion.div>

          {detailItems.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {detailItems.map(({ icon: Icon, label, value, isLink }) => (
                <motion.div key={label} variants={itemVariants} className="app-card p-5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl border border-primary-100 bg-primary-50 dark:border-violet-900/40 dark:bg-violet-950/30">
                      <Icon className="h-5 w-5 text-primary-600 dark:text-violet-400" aria-hidden="true" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">{label}</p>
                      {isLink ? (
                        <a href={value.startsWith('http') ? value : `https://${value}`}
                          target="_blank" rel="noopener noreferrer"
                          className="truncate text-sm font-semibold text-primary-700 hover:underline dark:text-violet-400">
                          {value}
                        </a>
                      ) : (
                        <p className="truncate text-sm font-semibold text-slate-950 dark:text-slate-100">{value}</p>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {!profile?.company && !profile?.website && !profile?.headline && (
            <motion.div variants={itemVariants}
              className="mt-4 rounded-2xl border border-dashed border-primary-200 bg-primary-50/40 p-6 text-center dark:border-violet-800/30 dark:bg-violet-950/10">
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Your profile is looking a little bare. Fill in your headline, company, and website.
              </p>
              <Link to="/profile/edit" className="mt-3 inline-flex app-button-secondary app-button-compact">
                <Edit3 className="h-4 w-4" aria-hidden="true" />
                Complete Profile
              </Link>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
