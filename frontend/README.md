## Frontend Structure

This folder is organized to keep routes stable while separating concerns:

- `*.html`: page entry files used directly by backend routes.
- `styles/`: all CSS files.
- `scripts/`: all JavaScript modules.
- `assets/`: logos and static media.

### Why HTML files stay at root

Backend routes currently serve these files directly:

- `landing.html`
- `blog.html`
- `contact.html`
- `index.html` (workspace via `/app/`)

Keeping HTML files at root avoids breaking existing URLs and route behavior.
