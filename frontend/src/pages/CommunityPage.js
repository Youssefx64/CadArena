import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowDown,
  ArrowUp,
  Building2,
  CheckCircle2,
  Clock,
  Eye,
  Filter,
  MessageCircle,
  PlusCircle,
  RefreshCw,
  Search,
  Send,
  Tag,
  User,
} from 'lucide-react';
import toast from 'react-hot-toast';
import cadArenaAPI from '../services/api';

const AUTHOR_STORAGE_KEY = 'cadarena_community_author_name';

const disciplines = [
  { value: 'all', label: 'All fields' },
  { value: 'architecture', label: 'Architecture' },
  { value: 'civil', label: 'Civil' },
  { value: 'structural', label: 'Structural' },
  { value: 'construction', label: 'Construction' },
  { value: 'mep', label: 'MEP' },
  { value: 'materials', label: 'Materials' },
  { value: 'surveying', label: 'Surveying' },
];

const sortOptions = [
  { value: 'active', label: 'Active' },
  { value: 'newest', label: 'Newest' },
  { value: 'score', label: 'Score' },
  { value: 'unanswered', label: 'Unanswered' },
];

const formatDate = (value) => {
  if (!value) {
    return 'Just now';
  }
  try {
    return new Intl.DateTimeFormat('en', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  } catch (_error) {
    return value;
  }
};

const parseTags = (value) => (
  value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
    .slice(0, 5)
);

const questionExcerpt = (body) => {
  const cleaned = String(body || '').replace(/\s+/g, ' ').trim();
  return cleaned.length > 180 ? `${cleaned.slice(0, 180)}...` : cleaned;
};

function VoteButtons({ score, onVote, disabled }) {
  return (
    <div className="flex w-14 shrink-0 flex-col items-center rounded-card border border-slate-200 bg-white/72 py-2 shadow-soft">
      <button
        type="button"
        onClick={() => onVote(1)}
        disabled={disabled}
        className="rounded-full p-1.5 text-slate-500 transition-colors hover:bg-primary-50 hover:text-primary-700 disabled:cursor-not-allowed disabled:opacity-40"
        aria-label="Upvote"
      >
        <ArrowUp className="h-4 w-4" />
      </button>
      <span className="py-1 text-sm font-black text-slate-950">{score}</span>
      <button
        type="button"
        onClick={() => onVote(-1)}
        disabled={disabled}
        className="rounded-full p-1.5 text-slate-500 transition-colors hover:bg-rose-50 hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-40"
        aria-label="Downvote"
      >
        <ArrowDown className="h-4 w-4" />
      </button>
    </div>
  );
}

export default function CommunityPage() {
  const [questions, setQuestions] = useState([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [postingQuestion, setPostingQuestion] = useState(false);
  const [postingAnswer, setPostingAnswer] = useState(false);
  const [voting, setVoting] = useState(false);
  const [filters, setFilters] = useState({
    query: '',
    tag: '',
    discipline: 'all',
    sort: 'active',
  });
  const [authorName, setAuthorName] = useState(() => {
    try {
      return localStorage.getItem(AUTHOR_STORAGE_KEY) || '';
    } catch (_error) {
      return '';
    }
  });
  const [questionForm, setQuestionForm] = useState({
    title: '',
    body: '',
    tags: '',
    discipline: 'architecture',
  });
  const [answerBody, setAnswerBody] = useState('');

  const selectedQuestion = detail?.question || questions.find((item) => item.id === selectedQuestionId) || null;
  const popularTags = useMemo(() => {
    const counts = new Map();
    questions.forEach((question) => {
      (question.tags || []).forEach((tag) => counts.set(tag, (counts.get(tag) || 0) + 1));
    });
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 8);
  }, [questions]);

  useEffect(() => {
    try {
      if (authorName.trim()) {
        localStorage.setItem(AUTHOR_STORAGE_KEY, authorName.trim());
      }
    } catch (_error) {
      // best effort persistence
    }
  }, [authorName]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadQuestions();
    }, 220);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.query, filters.tag, filters.discipline, filters.sort]);

  useEffect(() => {
    if (selectedQuestionId) {
      loadQuestionDetail(selectedQuestionId);
    } else {
      setDetail(null);
    }
  }, [selectedQuestionId]);

  const loadQuestions = async () => {
    setLoadingQuestions(true);
    try {
      const payload = await cadArenaAPI.listCommunityQuestions(filters);
      const nextQuestions = payload.questions || [];
      setQuestions(nextQuestions);
      setSelectedQuestionId((currentId) => {
        if (currentId && nextQuestions.some((question) => question.id === currentId)) {
          return currentId;
        }
        return nextQuestions[0]?.id || null;
      });
    } catch (error) {
      toast.error(error.message || 'Could not load community questions.');
    } finally {
      setLoadingQuestions(false);
    }
  };

  const loadQuestionDetail = async (questionId) => {
    setLoadingDetail(true);
    try {
      const payload = await cadArenaAPI.getCommunityQuestion(questionId);
      setDetail(payload);
    } catch (error) {
      toast.error(error.message || 'Could not load this question.');
      setDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  const refreshCurrentQuestion = async () => {
    await loadQuestions();
    if (selectedQuestionId) {
      await loadQuestionDetail(selectedQuestionId);
    }
  };

  const handleQuestionSubmit = async (event) => {
    event.preventDefault();
    const cleanedAuthor = authorName.trim();
    if (!cleanedAuthor) {
      toast.error('Add your name before posting.');
      return;
    }
    if (!questionForm.title.trim() || !questionForm.body.trim()) {
      toast.error('Question title and body are required.');
      return;
    }

    setPostingQuestion(true);
    try {
      const created = await cadArenaAPI.createCommunityQuestion({
        author_name: cleanedAuthor,
        title: questionForm.title,
        body: questionForm.body,
        tags: parseTags(questionForm.tags),
        discipline: questionForm.discipline,
      });
      toast.success('Question posted.');
      setQuestionForm({
        title: '',
        body: '',
        tags: '',
        discipline: questionForm.discipline,
      });
      await loadQuestions();
      setSelectedQuestionId(created.id);
    } catch (error) {
      toast.error(error.message || 'Could not post the question.');
    } finally {
      setPostingQuestion(false);
    }
  };

  const handleAnswerSubmit = async (event) => {
    event.preventDefault();
    if (!selectedQuestionId) {
      return;
    }
    const cleanedAuthor = authorName.trim();
    if (!cleanedAuthor) {
      toast.error('Add your name before answering.');
      return;
    }
    if (!answerBody.trim()) {
      toast.error('Answer body is required.');
      return;
    }

    setPostingAnswer(true);
    try {
      await cadArenaAPI.createCommunityAnswer(selectedQuestionId, {
        author_name: cleanedAuthor,
        body: answerBody,
      });
      setAnswerBody('');
      toast.success('Answer posted.');
      await refreshCurrentQuestion();
    } catch (error) {
      toast.error(error.message || 'Could not post the answer.');
    } finally {
      setPostingAnswer(false);
    }
  };

  const handleQuestionVote = async (direction) => {
    if (!selectedQuestionId || voting) {
      return;
    }
    setVoting(true);
    try {
      await cadArenaAPI.voteCommunityQuestion(selectedQuestionId, direction);
      await refreshCurrentQuestion();
    } catch (error) {
      toast.error(error.message || 'Vote failed.');
    } finally {
      setVoting(false);
    }
  };

  const handleAnswerVote = async (answerId, direction) => {
    if (voting) {
      return;
    }
    setVoting(true);
    try {
      await cadArenaAPI.voteCommunityAnswer(answerId, direction);
      if (selectedQuestionId) {
        await loadQuestionDetail(selectedQuestionId);
      }
    } catch (error) {
      toast.error(error.message || 'Vote failed.');
    } finally {
      setVoting(false);
    }
  };

  return (
    <div className="app-page">
      <div className="app-shell">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]"
        >
          <div>
            <span className="app-eyebrow">CadArena Community</span>
            <h1 className="app-page-title mt-3 max-w-4xl">
              Engineering Q&A for civil and architectural decisions.
            </h1>
          </div>
          <div className="app-card-muted p-5">
            <label className="mb-2 block text-sm font-bold text-slate-950" htmlFor="community-author-name">
              Posting name
            </label>
            <div className="flex items-center gap-3">
              <User className="h-5 w-5 shrink-0 text-primary-600" />
              <input
                id="community-author-name"
                value={authorName}
                onChange={(event) => setAuthorName(event.target.value)}
                className="app-input"
                maxLength={120}
                placeholder="e.g. Youssef Taha"
              />
            </div>
          </div>
        </motion.div>

        <div className="grid gap-6 xl:grid-cols-[minmax(340px,440px)_minmax(0,1fr)]">
          <aside className="space-y-5">
            <form onSubmit={(event) => event.preventDefault()} className="app-card p-5">
              <div className="mb-4 flex items-center gap-2 text-sm font-black text-slate-950">
                <Filter className="h-4 w-4 text-primary-600" />
                Board filters
              </div>
              <div className="space-y-3">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    value={filters.query}
                    onChange={(event) => setFilters((current) => ({ ...current, query: event.target.value }))}
                    className="app-input pl-11"
                    placeholder="Search questions"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <select
                    value={filters.discipline}
                    onChange={(event) => setFilters((current) => ({ ...current, discipline: event.target.value }))}
                    className="app-select"
                    aria-label="Discipline"
                  >
                    {disciplines.map((item) => (
                      <option key={item.value} value={item.value}>{item.label}</option>
                    ))}
                  </select>
                  <select
                    value={filters.sort}
                    onChange={(event) => setFilters((current) => ({ ...current, sort: event.target.value }))}
                    className="app-select"
                    aria-label="Sort"
                  >
                    {sortOptions.map((item) => (
                      <option key={item.value} value={item.value}>{item.label}</option>
                    ))}
                  </select>
                </div>
                <input
                  value={filters.tag}
                  onChange={(event) => setFilters((current) => ({ ...current, tag: event.target.value }))}
                  className="app-input"
                  placeholder="Filter by tag"
                />
              </div>

              {popularTags.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {popularTags.map(([tag, count]) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => setFilters((current) => ({ ...current, tag }))}
                      className="app-pill-muted py-2 text-xs"
                    >
                      <Tag className="h-3.5 w-3.5" />
                      {tag}
                      <span className="text-slate-400">{count}</span>
                    </button>
                  ))}
                </div>
              )}
            </form>

            <div className="space-y-3">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-sm font-black uppercase tracking-[0.18em] text-slate-500">
                  Questions
                </h2>
                <button
                  type="button"
                  onClick={refreshCurrentQuestion}
                  className="app-button-ghost app-button-compact min-h-10 px-3"
                  aria-label="Refresh questions"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>

              {loadingQuestions ? (
                [0, 1, 2].map((item) => (
                  <div key={item} className="app-card p-5">
                    <span className="app-skeleton mb-3 h-5 w-3/4" />
                    <span className="app-skeleton mb-4 h-4 w-full" />
                    <span className="app-skeleton h-9 w-40 app-skeleton-pill" />
                  </div>
                ))
              ) : questions.length === 0 ? (
                <div className="app-card-muted p-6 text-sm font-semibold text-slate-600">
                  No matching questions yet.
                </div>
              ) : (
                questions.map((question) => {
                  const active = question.id === selectedQuestionId;
                  return (
                    <button
                      key={question.id}
                      type="button"
                      onClick={() => setSelectedQuestionId(question.id)}
                      className={`community-question-card app-card w-full p-5 text-left ${active ? 'community-question-card-active' : ''}`}
                    >
                      <div className="mb-3 flex items-start justify-between gap-4">
                        <h3 className="line-clamp-2 text-base font-black leading-6 text-slate-950">
                          {question.title}
                        </h3>
                        <span className="rounded-full border border-primary-100 bg-primary-50 px-2.5 py-1 text-xs font-black text-primary-700">
                          {question.score}
                        </span>
                      </div>
                      <p className="mb-4 line-clamp-3 text-sm leading-6 text-slate-600">
                        {questionExcerpt(question.body)}
                      </p>
                      <div className="mb-4 flex flex-wrap gap-2">
                        {(question.tags || []).map((tag) => (
                          <span key={tag} className="app-pill-muted py-1.5 text-xs">
                            {tag}
                          </span>
                        ))}
                      </div>
                      <div className="flex flex-wrap items-center gap-3 text-xs font-bold text-slate-500">
                        <span className="inline-flex items-center gap-1">
                          <MessageCircle className="h-3.5 w-3.5" />
                          {question.answer_count}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Eye className="h-3.5 w-3.5" />
                          {question.view_count}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Building2 className="h-3.5 w-3.5" />
                          {question.discipline}
                        </span>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </aside>

          <main className="space-y-6">
            <form onSubmit={handleQuestionSubmit} className="app-card p-5 lg:p-6">
              <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                  <h2 className="app-card-title flex items-center gap-2">
                    <PlusCircle className="h-5 w-5 text-primary-600" />
                    Ask the community
                  </h2>
                </div>
                <select
                  value={questionForm.discipline}
                  onChange={(event) => setQuestionForm((current) => ({ ...current, discipline: event.target.value }))}
                  className="app-select max-w-[190px]"
                  aria-label="Question discipline"
                >
                  {disciplines.filter((item) => item.value !== 'all').map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
              </div>
              <div className="grid gap-3">
                <input
                  value={questionForm.title}
                  onChange={(event) => setQuestionForm((current) => ({ ...current, title: event.target.value }))}
                  className="app-input"
                  maxLength={160}
                  placeholder="Question title"
                />
                <textarea
                  value={questionForm.body}
                  onChange={(event) => setQuestionForm((current) => ({ ...current, body: event.target.value }))}
                  className="app-textarea min-h-[132px]"
                  maxLength={5000}
                  placeholder="Add drawings context, constraints, codes, loads, spans, materials, or site assumptions."
                />
                <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
                  <input
                    value={questionForm.tags}
                    onChange={(event) => setQuestionForm((current) => ({ ...current, tags: event.target.value }))}
                    className="app-input"
                    placeholder="tags: slabs, stairs, revit"
                  />
                  <button type="submit" disabled={postingQuestion} className="app-button-primary">
                    <Send className="h-4 w-4" />
                    <span>{postingQuestion ? 'Posting...' : 'Post question'}</span>
                  </button>
                </div>
              </div>
            </form>

            <section className="app-card-strong p-5 lg:p-6">
              {!selectedQuestion ? (
                <div className="py-16 text-center text-sm font-semibold text-slate-600">
                  Select a question to open the thread.
                </div>
              ) : loadingDetail && !detail ? (
                <div className="py-10">
                  <span className="app-skeleton mb-4 h-7 w-2/3" />
                  <span className="app-skeleton mb-3 h-4 w-full" />
                  <span className="app-skeleton h-4 w-3/4" />
                </div>
              ) : (
                <div className="space-y-6">
                  <article className="flex gap-4">
                    <VoteButtons score={selectedQuestion.score} onVote={handleQuestionVote} disabled={voting} />
                    <div className="min-w-0 flex-1">
                      <div className="mb-3 flex flex-wrap items-center gap-2">
                        {(selectedQuestion.tags || []).map((tag) => (
                          <span key={tag} className="app-pill-muted py-1.5 text-xs">{tag}</span>
                        ))}
                      </div>
                      <h2 className="text-2xl font-black leading-tight text-slate-950">
                        {selectedQuestion.title}
                      </h2>
                      <div className="mt-3 flex flex-wrap items-center gap-4 text-xs font-bold text-slate-500">
                        <span className="inline-flex items-center gap-1.5">
                          <User className="h-3.5 w-3.5" />
                          {selectedQuestion.author_name}
                        </span>
                        <span className="inline-flex items-center gap-1.5">
                          <Clock className="h-3.5 w-3.5" />
                          {formatDate(selectedQuestion.created_at)}
                        </span>
                        <span className="inline-flex items-center gap-1.5">
                          <Eye className="h-3.5 w-3.5" />
                          {selectedQuestion.view_count} views
                        </span>
                      </div>
                      <p className="mt-5 whitespace-pre-wrap text-[15px] leading-7 text-slate-700">
                        {selectedQuestion.body}
                      </p>
                    </div>
                  </article>

                  <div className="h-px bg-slate-200/80" />

                  <div className="space-y-4">
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="text-lg font-black text-slate-950">
                        {detail?.answers?.length || 0} answers
                      </h3>
                      {selectedQuestion.accepted_answer_id && (
                        <span className="app-pill py-2 text-xs">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Accepted
                        </span>
                      )}
                    </div>

                    {(detail?.answers || []).length === 0 ? (
                      <div className="app-card-muted p-5 text-sm font-semibold text-slate-600">
                        No answers yet.
                      </div>
                    ) : (
                      detail.answers.map((answer) => (
                        <article key={answer.id} className="flex gap-4 rounded-card border border-slate-200 bg-white/70 p-4 shadow-soft">
                          <VoteButtons
                            score={answer.score}
                            onVote={(direction) => handleAnswerVote(answer.id, direction)}
                            disabled={voting}
                          />
                          <div className="min-w-0 flex-1">
                            <p className="whitespace-pre-wrap text-[15px] leading-7 text-slate-700">
                              {answer.body}
                            </p>
                            <div className="mt-4 flex flex-wrap items-center gap-4 text-xs font-bold text-slate-500">
                              <span className="inline-flex items-center gap-1.5">
                                <User className="h-3.5 w-3.5" />
                                {answer.author_name}
                              </span>
                              <span className="inline-flex items-center gap-1.5">
                                <Clock className="h-3.5 w-3.5" />
                                {formatDate(answer.created_at)}
                              </span>
                            </div>
                          </div>
                        </article>
                      ))
                    )}
                  </div>

                  <form onSubmit={handleAnswerSubmit} className="rounded-card border border-primary-100 bg-primary-50/50 p-4">
                    <label className="mb-3 block text-sm font-black text-slate-950" htmlFor="community-answer">
                      Your answer
                    </label>
                    <textarea
                      id="community-answer"
                      value={answerBody}
                      onChange={(event) => setAnswerBody(event.target.value)}
                      className="app-textarea min-h-[132px]"
                      maxLength={5000}
                      placeholder="Reference assumptions, calculations, standards, field conditions, or coordination notes."
                    />
                    <div className="mt-3 flex justify-end">
                      <button type="submit" disabled={postingAnswer || !selectedQuestionId} className="app-button-primary">
                        <Send className="h-4 w-4" />
                        <span>{postingAnswer ? 'Posting...' : 'Post answer'}</span>
                      </button>
                    </div>
                  </form>
                </div>
              )}
            </section>
          </main>
        </div>
      </div>
    </div>
  );
}
