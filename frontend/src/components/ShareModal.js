import React, { useState } from 'react';
import { Share2, X, Copy, Check, Twitter, Linkedin, Facebook } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

export default function ShareModal({ question }) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const shareUrl = `${window.location.origin}/community/question/${question?.id}`;
  const shareText = `Check out this question on CadArena: "${question?.title}"`;

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    toast.success('Link copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = (platform) => {
    const urls = {
      twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
    };

    if (urls[platform]) {
      window.open(urls[platform], '_blank', 'width=600,height=400');
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
        title="Share this question"
      >
        <Share2 className="h-4 w-4" />
        Share
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-md rounded-card border border-slate-200 bg-white p-6 shadow-lg"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-bold text-slate-950">Share Question</h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="mb-6 space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-bold text-slate-950">
                    Share Link
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={shareUrl}
                      readOnly
                      className="app-input flex-1"
                    />
                    <button
                      onClick={handleCopy}
                      className="app-button-primary"
                    >
                      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="mb-3 block text-sm font-bold text-slate-950">
                    Share on Social Media
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    <button
                      onClick={() => handleShare('twitter')}
                      className="flex items-center justify-center gap-2 rounded-card border border-slate-200 bg-white p-3 transition-colors hover:bg-blue-50 hover:text-blue-600"
                      title="Share on Twitter"
                    >
                      <Twitter className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleShare('linkedin')}
                      className="flex items-center justify-center gap-2 rounded-card border border-slate-200 bg-white p-3 transition-colors hover:bg-blue-50 hover:text-blue-600"
                      title="Share on LinkedIn"
                    >
                      <Linkedin className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleShare('facebook')}
                      className="flex items-center justify-center gap-2 rounded-card border border-slate-200 bg-white p-3 transition-colors hover:bg-blue-50 hover:text-blue-600"
                      title="Share on Facebook"
                    >
                      <Facebook className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setIsOpen(false)}
                className="app-button-secondary w-full"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
