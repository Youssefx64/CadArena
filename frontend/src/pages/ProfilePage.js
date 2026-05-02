import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Edit3, Globe, Building2, Clock, Calendar, Mail,
  User, ExternalLink, MapPin, Pencil,
} from 'lucide-react';
import PropTypes from 'prop-types';
import { useAuth } from '../contexts/AuthContext';
import ProtectedRoute from '../components/auth/ProtectedRoute';

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.06, duration: 0.42, ease: [0.22, 1, 0.36, 1] },
  }),
};

function InfoRow({ icon: Icon, label, value, isLink }) {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-slate-100 dark:border-slate-700/40 last:border-0">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800">
        <Icon className="h-4 w-4 text-slate-500 dark:text-slate-400" aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-0.5">{label}</p>
        {isLink ? (
          <a
            href={value.startsWith('http') ? value : `https://${value}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm font-semibold text-primary-600 hover:text-primary-700 dark:text-violet-400 dark:hover:text-violet-300 truncate"
          >
            <span className="truncate">{value}</span>
            <ExternalLink className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
          </a>
        ) : (
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{value}</p>
        )}
      </div>
    </div>
  );
}

InfoRow.propTypes = {
  icon: PropTypes.elementType.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  isLink: PropTypes.bool,
};

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

  if (isLoading) {
    return (
      <div className="app-page">
        <div className="app-shell mx-auto max-w-2xl space-y-4">
          <div className="app-card app-card-strong overflow-hidden">
            <div className="h-28 bg-gradient-to-br from-primary-100 to-violet-100 dark:from-primary-950/60 dark:to-violet-950/60" />
            <div className="px-6 pb-6 -mt-14">
              <span className="app-skeleton block h-24 w-24 rounded-full border-4 border-white dark:border-slate-900 mb-4" />
              <span className="app-skeleton block h-7 w-44 mb-2" />
              <span className="app-skeleton block h-4 w-32" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  const infoItems = [
    { icon: Mail, label: 'Email', value: user?.email },
    { icon: Building2, label: 'Company', value: profile?.company },
    { icon: Globe, label: 'Website', value: profile?.website, isLink: true },
    { icon: MapPin, label: 'Timezone', value: profile?.timezone },
  ].filter((d) => !!d.value);

  const isProfileEmpty = !profile?.company && !profile?.website && !profile?.headline && !profile?.timezone;

  return (
    <div className="app-page">
      <div className="app-shell mx-auto max-w-2xl space-y-4">

        {/* Hero Card */}
        <motion.div custom={0} initial="hidden" animate="visible" variants={fadeUp}
          className="app-card app-card-strong overflow-hidden">

          {/* Banner */}
          <div className="relative h-32 bg-gradient-to-br from-primary-400 via-primary-500 to-violet-600 dark:from-primary-800 dark:via-primary-700 dark:to-violet-800">
            <div className="absolute inset-0 opacity-20"
              style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(255,255,255,0.3) 0%, transparent 60%), radial-gradient(circle at 80% 20%, rgba(255,255,255,0.2) 0%, transparent 50%)' }} />
            {/* Edit button top-right */}
            <Link
              to="/profile/edit"
              className="absolute top-3 right-3 flex items-center gap-1.5 rounded-full bg-white/20 backdrop-blur-sm border border-white/30 px-3 py-1.5 text-xs font-semibold text-white transition-all hover:bg-white/30"
              aria-label="Edit profile"
            >
              <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
              Edit Profile
            </Link>
          </div>

          {/* Avatar + Name */}
          <div className="px-6 pb-6">
            <div className="flex items-end justify-between -mt-12 mb-4">
              <div className="relative">
                {avatarImgError ? (
                  <div className="h-24 w-24 rounded-full border-4 border-white dark:border-slate-900 shadow-lg bg-primary-100 dark:bg-primary-950 flex items-center justify-center">
                    <User className="h-10 w-10 text-primary-400 dark:text-primary-600" aria-hidden="true" />
                  </div>
                ) : (
                  <img
                    key={avatarTs}
                    src={`/api/v1/profile/me/avatar?t=${avatarTs}`}
                    alt={displayName}
                    className="h-24 w-24 rounded-full border-4 border-white dark:border-slate-900 shadow-lg object-cover"
                    onError={() => setAvatarImgError(true)}
                  />
                )}
                <Link
                  to="/profile/edit"
                  className="absolute -bottom-0.5 -right-0.5 flex h-7 w-7 items-center justify-center rounded-full border-2 border-white dark:border-slate-900 bg-primary-600 text-white shadow transition-colors hover:bg-primary-700"
                  aria-label="Change avatar"
                >
                  <Edit3 className="h-3.5 w-3.5" aria-hidden="true" />
                </Link>
              </div>
            </div>

            <h1 className="text-2xl font-black tracking-tight text-slate-950 dark:text-white">
              {displayName}
            </h1>

            {profile?.headline && (
              <p className="mt-1 text-sm font-medium text-primary-700 dark:text-violet-400">
                {profile.headline}
              </p>
            )}

            {profile?.company && (
              <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400">
                <Building2 className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
                {profile.company}
              </p>
            )}

            <div className="mt-3 flex flex-wrap gap-2">
              {joinDate && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 dark:bg-slate-800 px-3 py-1 text-xs font-medium text-slate-600 dark:text-slate-300">
                  <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
                  Joined {joinDate}
                </span>
              )}
              {profile?.timezone && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 dark:bg-slate-800 px-3 py-1 text-xs font-medium text-slate-600 dark:text-slate-300">
                  <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                  {profile.timezone}
                </span>
              )}
            </div>
          </div>
        </motion.div>

        {/* Info Card */}
        {infoItems.length > 0 && (
          <motion.div custom={1} initial="hidden" animate="visible" variants={fadeUp}
            className="app-card app-card-strong px-6 py-2">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500 pt-4 pb-1">
              Contact & Details
            </p>
            {infoItems.map(({ icon, label, value, isLink }) => (
              <InfoRow key={label} icon={icon} label={label} value={value} isLink={isLink} />
            ))}
          </motion.div>
        )}

        {/* Empty state */}
        {isProfileEmpty && (
          <motion.div custom={2} initial="hidden" animate="visible" variants={fadeUp}
            className="rounded-2xl border border-dashed border-primary-200 dark:border-violet-800/40 bg-primary-50/50 dark:bg-violet-950/10 p-7 text-center">
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">
              Add your headline, company, and website to make your profile stand out.
            </p>
            <Link to="/profile/edit" className="app-button-secondary app-button-compact inline-flex">
              <Edit3 className="h-4 w-4" aria-hidden="true" />
              Complete Profile
            </Link>
          </motion.div>
        )}

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
