const fs = require('fs');
const path = require('path');

const SOURCE = path.resolve(__dirname, '../studio-source');
const DEST = path.resolve(__dirname, '../public/studio-app');

function copyDir(src, dest) {
  if (!fs.existsSync(src)) {
    return;
  }

  fs.mkdirSync(dest, { recursive: true });

  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function patchStaticPaths(html) {
  return html
    .replace(/href="\/static\/styles\//g, 'href="./styles/')
    .replace(/src="\/static\/scripts\//g, 'src="./scripts/')
    .replace(/src="\/static\/assets\//g, 'src="./assets/')
    .replace(/href="\/static\/assets\//g, 'href="./assets/')
    .replace(/href="\/app\/"/g, 'href="/studio"');
}

fs.rmSync(DEST, { recursive: true, force: true });
fs.mkdirSync(DEST, { recursive: true });

let html = fs.readFileSync(path.join(SOURCE, 'index.html'), 'utf8');
html = patchStaticPaths(html)
  .replace('class="topbar-brand" href="/"', 'class="topbar-brand" href="/" target="_top"')
  .replace('class="sidebar-mark" href="/"', 'class="sidebar-mark" href="/" target="_top"');

fs.writeFileSync(path.join(DEST, 'index.html'), html);

const profilePath = path.join(SOURCE, 'profile.html');
if (fs.existsSync(profilePath)) {
  const profileHtml = patchStaticPaths(fs.readFileSync(profilePath, 'utf8'))
    .replace('class="profile-brand" href="/"', 'class="profile-brand" href="./index.html"');
  fs.writeFileSync(path.join(DEST, 'profile.html'), profileHtml);
}

copyDir(path.join(SOURCE, 'scripts'), path.join(DEST, 'scripts'));
copyDir(path.join(SOURCE, 'styles'), path.join(DEST, 'styles'));
copyDir(path.join(SOURCE, 'assets'), path.join(DEST, 'assets'));

const appScriptPath = path.join(DEST, 'scripts', 'app.js');
if (fs.existsSync(appScriptPath)) {
  let appScript = fs.readFileSync(appScriptPath, 'utf8');
  appScript = appScript
    .replace('const DEFAULT_PROFILE_AVATAR = "/static/assets/cadarena-mark.svg";', 'const DEFAULT_PROFILE_AVATAR = "./assets/cadarena-mark.svg";')
    .replace('window.location.href = "/app/profile.html";', 'window.location.href = "./profile.html";');
  fs.writeFileSync(appScriptPath, appScript);
}

const profileScriptPath = path.join(DEST, 'scripts', 'profile.js');
if (fs.existsSync(profileScriptPath)) {
  let profileScript = fs.readFileSync(profileScriptPath, 'utf8');
  profileScript = profileScript
    .replace('const DEFAULT_PROFILE_AVATAR = "/static/assets/cadarena-mark.svg";', 'const DEFAULT_PROFILE_AVATAR = "./assets/cadarena-mark.svg";')
    .replace('window.location.href = "/app/?auth=login";', 'window.location.href = "./index.html?auth=login";')
    .replace('window.location.href = "/app/";', 'window.location.href = "./index.html";');
  fs.writeFileSync(profileScriptPath, profileScript);
}

const backNavScriptPath = path.join(DEST, 'scripts', 'back-nav.js');
if (fs.existsSync(backNavScriptPath)) {
  let backNavScript = fs.readFileSync(backNavScriptPath, 'utf8');
  backNavScript = backNavScript.replace(
    `  button.addEventListener("click", () => {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }

    if (document.referrer) {
      try {
        const referrerUrl = new URL(document.referrer);
        if (referrerUrl.origin === window.location.origin) {
          window.location.href = document.referrer;
          return;
        }
      } catch (_error) {
        // invalid referrer, fallback to home
      }
    }

    window.location.href = "/";
  });`,
    `  button.addEventListener("click", () => {
    const inIframe = window.top && window.top !== window;

    if (inIframe) {
      try {
        const referrerUrl = document.referrer ? new URL(document.referrer) : null;
        const sameStudioFrame =
          referrerUrl &&
          referrerUrl.origin === window.location.origin &&
          referrerUrl.pathname.startsWith("/studio-app/");

        if (sameStudioFrame && window.history.length > 1) {
          window.history.back();
          return;
        }

        if (window.top.history.length > 1) {
          window.top.history.back();
          return;
        }
      } catch (_error) {
        // ignore cross-frame history issues and fallback to home
      }

      window.top.location.href = "/";
      return;
    }

    if (window.history.length > 1) {
      window.history.back();
      return;
    }

    if (document.referrer) {
      try {
        const referrerUrl = new URL(document.referrer);
        if (referrerUrl.origin === window.location.origin) {
          window.location.href = document.referrer;
          return;
        }
      } catch (_error) {
        // invalid referrer, fallback to home
      }
    }

    window.location.href = "/";
  });`
  );
  fs.writeFileSync(backNavScriptPath, backNavScript);
}

console.log('[copy-studio] Studio files copied to public/studio-app/');
