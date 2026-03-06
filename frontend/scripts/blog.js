import { initPageMotion } from "./page-motion.js";

const STORAGE_KEY = "cadarena_blog_posts_v1";

const form = document.getElementById("blog-form");
const titleInput = document.getElementById("post-title");
const projectInput = document.getElementById("post-project");
const summaryInput = document.getElementById("post-summary");
const contentInput = document.getElementById("post-content");
const statusNode = document.getElementById("form-status");
const postsList = document.getElementById("posts-list");
const clearFormBtn = document.getElementById("clear-form");
const clearAllBtn = document.getElementById("clear-all");

initPageMotion({
  navSelector: ".blog-nav",
  revealSelector: ".motion-reveal",
});

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function readPosts() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function savePosts(posts) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(posts));
}

function setStatus(message) {
  if (statusNode) {
    statusNode.textContent = message;
  }
}

function clearForm() {
  if (form) {
    form.reset();
  }
  setStatus("Form cleared.");
}

function formatDate(isoValue) {
  try {
    const date = new Date(isoValue);
    return date.toLocaleString();
  } catch {
    return isoValue;
  }
}

function renderPosts() {
  if (!postsList) {
    return;
  }

  const posts = readPosts();

  if (posts.length === 0) {
    postsList.innerHTML = '<p class="empty-state post-enter" style="--post-delay: 0ms;">No blog posts yet. Publish your first update.</p>';
    return;
  }

  postsList.innerHTML = posts
    .map(
      (post, index) => `
        <article class="post-card post-enter" style="--post-delay:${Math.min(index * 45, 260)}ms" data-id="${post.id}">
          <div class="post-head">
            <div>
              <h3 class="post-title">${escapeHtml(post.title)}</h3>
              <p class="post-meta">Project: ${escapeHtml(post.project)} · ${escapeHtml(formatDate(post.createdAt))}</p>
            </div>
            <button class="post-delete" type="button" data-action="delete" data-id="${post.id}">Delete</button>
          </div>
          ${post.summary ? `<p class="post-summary">${escapeHtml(post.summary)}</p>` : ""}
          <p class="post-content">${escapeHtml(post.content)}</p>
        </article>
      `,
    )
    .join("");
}

function createPost() {
  const title = titleInput?.value.trim() || "";
  const project = projectInput?.value.trim() || "";
  const summary = summaryInput?.value.trim() || "";
  const content = contentInput?.value.trim() || "";

  if (!title || !project || !content) {
    setStatus("Title, project name, and content are required.");
    return;
  }

  const posts = readPosts();
  const post = {
    id: crypto.randomUUID(),
    title,
    project,
    summary,
    content,
    createdAt: new Date().toISOString(),
  };

  posts.unshift(post);
  savePosts(posts);
  renderPosts();
  form?.reset();
  setStatus("Post published successfully.");
}

function deletePost(postId) {
  const posts = readPosts();
  const nextPosts = posts.filter((post) => post.id !== postId);
  savePosts(nextPosts);
  renderPosts();
  setStatus("Post deleted.");
}

function clearAllPosts() {
  const confirmed = window.confirm("Delete all blog posts?");
  if (!confirmed) {
    return;
  }
  savePosts([]);
  renderPosts();
  setStatus("All posts removed.");
}

form?.addEventListener("submit", (event) => {
  event.preventDefault();
  createPost();
});

clearFormBtn?.addEventListener("click", () => {
  clearForm();
});

clearAllBtn?.addEventListener("click", () => {
  clearAllPosts();
});

postsList?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }

  const action = target.dataset.action;
  if (action !== "delete") {
    return;
  }

  const postId = target.dataset.id;
  if (!postId) {
    return;
  }

  deletePost(postId);
});

renderPosts();
