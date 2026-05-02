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
    <div className="flex items-start gap-3 py-3 border-b border-slate-100 dark:border-slate-700/40 last:border-0">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 mt-0.5">
        <Icon className="h-4 w-4 text-slate-500 dark:text-slate-400" aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-0.5">{label}</p>
        {isLink ? (
          <a
            href={value.startsWith('http') ? value : `https://${value}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-start gap-1 text-sm font-semibold text-primary-600 hover:text-primary-700 dark:text-violet-400 dark:hover:text-violet-300 break-all"
          >
            <span>{value}</span>
            <ExternalLink className="h-3 w-3 flex-shrink-0 mt-0.5" aria-hidden="true" />
          </a>
        ) : (
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 break-words">{value}</p>
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

function AvatarCircle({ avatarUrl, avatarTs, displayName }) {
  const [imgError, setImgError] = useState(false);

  const hasAvatar = !!avatarUrl && !imgError;

  return hasAvatar ? (
    <img
      key={avatarTs}
      src={`${avatarUrl}?t=${avatarTs}`}
      alt={displayName}
      className="h-24 w-24 rounded-full border-4 border-white dark:border-slate-900 shadow-lg object-cover"
      onError={() => setImgError(true)}
    />
  ) : (
    <div className="h-24 w-24 rounded-full border-4 border-white dark:border-slate-900 shadow-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
      <User className="h-10 w-10 text-slate-400 dark:text-slate-500" aria-hidden="true" />
    </div>
  );
}

AvatarCircle.propTypes = {
  avatarUrl: PropTypes.string,
  avatarTs: PropTypes.number.isRequired,
  displayName: PropTypes.string.isRequired,
};

function ProfileContent() {
  const { user, profile, refreshProfile, avatarTs } = useAuth();
  const [isLoading, setIsLoading] = useState(!profile);

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
          <div className="app-card app-card-strong overflow-hidden rounded-3xl">
            <div className="h-28" style={{ background: 'linear-gradient(135deg, #6366f1 0%, #7c3aed 100%)' }} />
            <div className="px-6 pb-6 -mt-12">
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
          <div
            className="relative h-32"
            style={{ background: 'linear-gradient(135deg, #6366f1 0%, #818cf8 40%, #7c3aed 100%)' }}
          >
            <div
              className="absolute inset-0 pointer-events-none"
              style={{ background: 'radial-gradient(circle at 15% 50%, rgba(255,255,255,0.18) 0%, transparent 55%), radial-gradient(circle at 85% 20%, rgba(255,255,255,0.12) 0%, transparent 45%)' }}
            />
            <Link
              to="/profile/edit"
              className="absolute top-3 right-3 flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold text-white transition-all"
              style={{ background: 'rgba(255,255,255,0.18)', border: '1px solid rgba(255,255,255,0.28)', backdropFilter: 'blur(8px)' }}
              aria-label="Edit profile"
            >
              <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
              Edit Profile
            </Link>
          </div>

          {/* Avatar + Info */}
          <div className="px-6 pb-6">
            <div className="flex items-end justify-between -mt-12 mb-4">
              <div className="relative">
                <AvatarCircle avatarUrl={profile?.avatar_url} avatarTs={avatarTs} displayName={displayName} />
                <Link
                  to="/profile/edit"
                  className="absolute -bottom-0.5 -right-0.5 flex h-7 w-7 items-center justify-center rounded-full border-2 border-white dark:border-slate-900 bg-indigo-600 text-white shadow transition-colors hover:bg-indigo-700"
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
              <p className="mt-1 text-sm font-semibold text-indigo-600 dark:text-violet-400">
                {profile.headline}
              </p>
            )}

            {profile?.company && (
              <p className="mt-1.5 flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400">
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
            <div className="pb-2" />
          </motion.div>
        )}

        {/* Empty state */}
        {isProfileEmpty && (
          <motion.div custom={2} initial="hidden" animate="visible" variants={fadeUp}
            className="rounded-2xl border border-dashed border-indigo-200 dark:border-violet-800/40 bg-indigo-50/50 dark:bg-violet-950/10 p-7 text-center">
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
