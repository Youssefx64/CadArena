import React from 'react';
import { motion } from 'framer-motion';
import { Search, MessageSquare, Eye, ArrowUp, PlusCircle, Tag, Layers } from 'lucide-react';
import cadArenaAPI from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const disciplines = ['all', 'architecture', 'civil', 'structural', 'construction', 'mep', 'materials', 'surveying', 'general'];

export default function CommunityPage() {
  const { user } = useAuth();
  const [query, setQuery] = React.useState('');
  const [discipline, setDiscipline] = React.useState('all');
  const [questions, setQuestions] = React.useState([]);
  const [selected, setSelected] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [newTitle, setNewTitle] = React.useState('');
  const [newBody, setNewBody] = React.useState('');
  const [newTags, setNewTags] = React.useState('');
  const [posting, setPosting] = React.useState(false);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await cadArenaAPI.listCommunityQuestions({ query, discipline, limit: 40, sort: 'active' });
      setQuestions(res.questions || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [query, discipline]);

  React.useEffect(() => {
    load();
  }, [load]);

  const openQuestion = async (id) => {
    try {
      const detail = await cadArenaAPI.getCommunityQuestion(id);
      setSelected(detail);
    } catch (err) {
      setError(err.message);
    }
  };

  const submitQuestion = async (e) => {
    e.preventDefault();
    setPosting(true);
    setError('');
    try {
      await cadArenaAPI.createCommunityQuestion({
        title: newTitle,
        body: newBody,
        tags: newTags.split(',').map((t) => t.trim()).filter(Boolean),
        discipline: discipline === 'all' ? 'general' : discipline,
        author_name: user?.name || undefined,
      });
      setNewTitle('');
      setNewBody('');
      setNewTags('');
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="app-page">
      <div className="app-shell space-y-6">
        <div className="app-page-header">
          <span className="app-pill"><Layers className="h-4 w-4" /> Engineering Community</span>
          <h1 className="app-page-title">Ask, share, and review designs together</h1>
          <p className="app-page-copy">A professional civil/architectural network for discussions, critiques, and practical troubleshooting.</p>
        </div>

        {error && <div className="rag-notice rag-notice-error">{error}</div>}

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
          <section className="xl:col-span-4 app-card p-5">
            <h2 className="app-card-title mb-4 flex items-center gap-2"><PlusCircle className="h-4 w-4" /> Create a post</h2>
            <form onSubmit={submitQuestion} className="space-y-3">
              <input className="app-input w-full" placeholder="Post title" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} required minLength={8} />
              <textarea className="app-textarea w-full min-h-[140px]" placeholder="Describe your issue, design, or question..." value={newBody} onChange={(e) => setNewBody(e.target.value)} required minLength={20} />
              <input className="app-input w-full" placeholder="Tags (comma separated)" value={newTags} onChange={(e) => setNewTags(e.target.value)} />
              <button type="submit" className="app-button-primary w-full" disabled={posting}>{posting ? 'Publishing...' : 'Publish question'}</button>
            </form>
          </section>

          <section className="xl:col-span-8 space-y-4">
            <div className="app-card p-4 flex flex-col gap-3 md:flex-row md:items-center">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input className="app-input w-full pl-10" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by title, body, tag..." />
              </div>
              <select className="app-input md:w-56" value={discipline} onChange={(e) => setDiscipline(e.target.value)}>
                {disciplines.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>

            <div className="space-y-3">
              {loading ? (
                <div className="app-card p-5">Loading community feed...</div>
              ) : questions.length === 0 ? (
                <div className="app-card p-5">No posts yet. Be the first one to ask.</div>
              ) : (
                questions.map((q) => (
                  <motion.button
                    key={q.id}
                    type="button"
                    whileHover={{ y: -2 }}
                    onClick={() => openQuestion(q.id)}
                    className="app-card app-card-hover w-full p-5 text-left"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-base font-black text-slate-900 dark:text-slate-50">{q.title}</h3>
                      <span className="app-pill-muted">{q.discipline}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 line-clamp-2">{q.body}</p>
                    <div className="mt-3 flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-500 dark:text-slate-400">
                      <span className="inline-flex items-center gap-1"><ArrowUp className="h-3.5 w-3.5" /> {q.score}</span>
                      <span className="inline-flex items-center gap-1"><MessageSquare className="h-3.5 w-3.5" /> {q.answer_count}</span>
                      <span className="inline-flex items-center gap-1"><Eye className="h-3.5 w-3.5" /> {q.view_count}</span>
                      {(q.tags || []).slice(0, 3).map((tag) => (
                        <span key={tag} className="inline-flex items-center gap-1 app-pill-muted"><Tag className="h-3 w-3" /> {tag}</span>
                      ))}
                    </div>
                  </motion.button>
                ))
              )}
            </div>
          </section>
        </div>

        {selected && (
          <div className="app-card p-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="app-card-title">{selected.question.title}</h2>
              <button className="app-button-ghost" onClick={() => setSelected(null)}>Close</button>
            </div>
            <p className="app-body">{selected.question.body}</p>
            <div className="mt-6 space-y-3">
              <h3 className="font-bold text-slate-900 dark:text-slate-100">Answers</h3>
              {(selected.answers || []).length === 0 ? (
                <p className="text-sm text-slate-500 dark:text-slate-400">No answers yet.</p>
              ) : (
                selected.answers.map((a) => (
                  <div key={a.id} className="app-card-muted p-4">
                    <p className="text-sm leading-7 text-slate-700 dark:text-slate-300">{a.body}</p>
                    <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">By {a.author_name}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
