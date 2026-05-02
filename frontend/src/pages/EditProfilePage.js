import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Trash2, Save, ArrowLeft, User, Globe, Building2, Clock, Sparkles, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import authApi from '../services/authApi';
import ProtectedRoute from '../components/auth/ProtectedRoute';

const FORM_FIELDS = [
  { name: 'display_name', label: 'Display Name', type: 'text', icon: User, placeholder: 'How should we call you?', hint: 'Shown publicly on your profile.' },
  { name: 'headline', label: 'Headline', type: 'text', icon: Sparkles, placeholder: 'e.g. Architectural Designer · BIM Specialist', hint: 'A brief description of your role.' },
  { name: 'company', label: 'Company', type: 'text', icon: Building2, placeholder: 'Where do you work?' },
  { name: 'website', label: 'Website', type: 'url', icon: Globe, placeholder: 'https://yoursite.com' },
  { name: 'timezone', label: 'Timezone', type: 'text', icon: Clock, placeholder: 'e.g. UTC+3, Africa/Cairo' },
];

function EditProfileContent() {
  const { user, profile, refreshProfile, avatarTs, bumpAvatarTs } = useAuth();
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const [fields, setFields]             = useState({ display_name: '', headline: '', company: '', website: '', timezone: '' });
  const [isSaving, setIsSaving]         = useState(false);
  const [isUploadingAvatar, setUploading] = useState(false);
  const [isDeletingAvatar, setDeleting]   = useState(false);
  const [avatarPreview, setPreview]     = useState(null);
  const [avatarImgError, setAvatarImgError] = useState(false);
  const [apiError, setApiError]         = useState('');

  useEffect(() => {
    if (!profile) {
      refreshProfile();
    }
  }, [profile, refreshProfile]);

  useEffect(() => {
    if (profile) {
      setFields({
        display_name: profile.display_name || user?.name || '',
        headline:     profile.headline     || '',
        company:      profile.company      || '',
        website:      profile.website      || '',
        timezone:     profile.timezone     || '',
      });
    }
  }, [profile, user]);

  useEffect(() => {
    return () => { if (avatarPreview) URL.revokeObjectURL(avatarPreview); };
  }, [avatarPreview]);

  const onFieldChange = (e) => {
    setFields((f) => ({ ...f, [e.target.name]: e.target.value }));
    setApiError('');
  };

  const onSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setApiError('');
    try {
      await authApi.updateProfile(fields);
      await refreshProfile();
      toast.success('Profile updated!');
      navigate('/profile');
    } catch (err) {
      setApiError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const onAvatarFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    setUploading(true);
    try {
      await authApi.uploadAvatar(file);
      bumpAvatarTs();
      toast.success('Avatar updated!');
    } catch (err) {
      toast.error(`Upload failed: ${err.message}`);
      setPreview(null);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const onDeleteAvatar = async () => {
    setDeleting(true);
    setPreview(null);
    try {
      await authApi.deleteAvatar();
      bumpAvatarTs();
      toast.success('Avatar removed.');
    } catch (err) {
      toast.error(`Could not remove avatar: ${err.message}`);
    } finally {
      setDeleting(false);
    }
  };

  const hasRealAvatar = !!avatarPreview || !!profile?.avatar_url;
  const currentAvatarSrc = avatarPreview || (profile?.avatar_url ? `${profile.avatar_url}?t=${avatarTs}` : null);

  return (
    <div className="app-page">
      <div className="app-shell mx-auto max-w-2xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.32 }}>
          <div className="mb-6 flex items-center gap-3">
            <Link to="/profile" className="app-button-ghost app-button-compact">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Back
            </Link>
            <div>
              <h1 className="text-xl font-black tracking-tight text-slate-950 dark:text-slate-50">Edit Profile</h1>
              <p className="text-sm text-slate-500 dark:text-slate-400">Update your information and avatar</p>
            </div>
          </div>

          <div className="app-card app-card-strong mb-5 p-6">
            <h2 className="mb-4 text-xs font-bold uppercase tracking-widest text-slate-400">Profile Picture</h2>
            <div className="flex flex-col items-center gap-5 sm:flex-row">
              <div className="relative h-24 w-24 flex-shrink-0">
                {hasRealAvatar && !avatarImgError ? (
                  <img
                    key={avatarPreview || avatarTs}
                    src={currentAvatarSrc}
                    alt=""
                    className="h-24 w-24 rounded-full border-4 border-slate-200 dark:border-slate-700 object-cover shadow-md"
                    onError={() => setAvatarImgError(true)}
                  />
                ) : (
                  <div className="h-24 w-24 rounded-full border-4 border-slate-200 dark:border-slate-700 shadow-md bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                    <User className="h-10 w-10 text-slate-400 dark:text-slate-500" aria-hidden="true" />
                  </div>
                )}
                <AnimatePresence>
                  {(isUploadingAvatar || isDeletingAvatar) && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      className="absolute inset-0 flex items-center justify-center rounded-full bg-black/45">
                      <motion.div className="h-6 w-6 rounded-full border-2 border-white border-t-transparent"
                        animate={{ rotate: 360 }} transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }} aria-hidden="true" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="flex flex-col gap-3 text-center sm:text-left">
                <p className="text-sm leading-relaxed text-slate-500 dark:text-slate-400">
                  Square image, minimum 128 × 128 px · Max 5 MB
                  <br />
                  PNG, JPG, WEBP, or GIF
                </p>
                <div className="flex flex-wrap justify-center gap-2 sm:justify-start">
                  <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp,image/gif"
                    onChange={onAvatarFileChange} className="sr-only" aria-label="Upload new profile picture" />
                  <button type="button" onClick={() => fileRef.current?.click()}
                    disabled={isUploadingAvatar || isDeletingAvatar}
                    className="app-button-secondary app-button-compact">
                    <Camera className="h-4 w-4" aria-hidden="true" />
                    Upload Photo
                  </button>
                  <button type="button" onClick={onDeleteAvatar}
                    disabled={isUploadingAvatar || isDeletingAvatar}
                    className="inline-flex items-center gap-2 rounded-full border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-semibold text-red-700 transition-colors hover:bg-red-100 disabled:opacity-50 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-400 dark:hover:bg-red-950/50">
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                    Remove
                  </button>
                </div>
              </div>
            </div>
          </div>

          <form onSubmit={onSave}>
            <div className="app-card app-card-strong p-6">
              <h2 className="mb-5 text-xs font-bold uppercase tracking-widest text-slate-400">Profile Information</h2>

              <AnimatePresence>
                {apiError && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                    className="mb-5 flex items-start gap-3 overflow-hidden rounded-2xl border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/30"
                    role="alert" aria-live="polite">
                    <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" aria-hidden="true" />
                    <p className="text-sm font-semibold text-red-700">{apiError}</p>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="space-y-5">
                {FORM_FIELDS.map(({ name, label, type, icon: Icon, placeholder, hint }) => (
                  <div key={name}>
                    <label htmlFor={`ep-${name}`} className="mb-1.5 block text-sm font-semibold text-slate-950 dark:text-slate-100">
                      {label}
                    </label>
                    <div className="relative">
                      <Icon className="pointer-events-none absolute left-4 top-1/2 z-10 h-5 w-5 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                      <input id={`ep-${name}`} type={type} name={name} value={fields[name]} onChange={onFieldChange}
                        placeholder={placeholder} autoComplete="off" className="app-input pl-11" disabled={isSaving} />
                    </div>
                    {hint && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{hint}</p>}
                  </div>
                ))}
              </div>

              <div className="mt-7 flex flex-col justify-end gap-3 border-t border-slate-100 pt-5 sm:flex-row dark:border-slate-700/50">
                <Link to="/profile" className="app-button-ghost app-button-compact w-full justify-center sm:w-auto">
                  Cancel
                </Link>
                <motion.button type="submit" disabled={isSaving}
                  whileHover={!isSaving ? { scale: 1.01 } : {}} whileTap={!isSaving ? { scale: 0.99 } : {}}
                  className="app-button-primary app-button-compact w-full justify-center sm:w-auto">
                  {isSaving ? (
                    <>
                      <motion.span className="block h-4 w-4 rounded-full border-2 border-white border-t-transparent"
                        animate={{ rotate: 360 }} transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }} aria-hidden="true" />
                      Saving…
                    </>
                  ) : (
                    <><Save className="h-4 w-4" aria-hidden="true" />Save Changes</>
                  )}
                </motion.button>
              </div>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
}

export default function EditProfilePage() {
  return (
    <ProtectedRoute>
      <EditProfileContent />
    </ProtectedRoute>
  );
}
