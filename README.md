# SearchChord project page

A static, responsive research project page ready for GitHub Pages. No package installation or build step is required.

## Contents

- `dist/`: the complete deployable page, 24 selected comparisons (12 PIE-Bench + 12 CropWeed), 96 byte-identical gallery images, separate header comparisons, full benchmark means, method overview, figure and BibTeX. The paper displays “update soon”; no manuscript PDF is provided.
- `.github/workflows/pages.yml`: deployment on pushes to `master` or `main`, or a manual workflow run.
- `prepare_assets.py`: reproducible packaging from the saved local experiment outputs. This script checks input hashes, metric records and saved manifests; it never runs inference or scoring.

## Preview locally

```sh
python -m http.server 8811 --bind 127.0.0.1 --directory dist
```

Visit `http://127.0.0.1:8811`. Serve through HTTP; opening `index.html` directly does not allow the browser to fetch the gallery JSON.

## Publish with GitHub Pages

1. Create the intended project repository and upload this project directory, including `.github` and `dist`.
2. Set the correct URLs in `dist/site-config.js`: `repositoryUrl` to the repository, and `siteUrl` to the actual published project page.
3. In repository **Settings → Pages**, choose **GitHub Actions** as the source.
4. Push to `master` (this repository's default branch) or `main`, or run the **Deploy project page to GitHub Pages** workflow.
5. Verify the URL returned by deployment. Project URLs normally have the form `https://OWNER.github.io/REPOSITORY/`. Use the verified URL when adding a link to the abstract.

Official instructions: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site

All page assets use relative URLs, so a repository subpath works. GitHub Pages is static hosting; the site has no server-side dependencies, analytics, or external fonts.

## Selection and interpretation

The two header examples are excluded from the expanded gallery. The gallery uses different saved edits while retaining 12 comparisons for each dataset.

The gallery emphasizes selected successes, as requested. Each displayed EditReward-cascade example improves saved PSNR, LPIPS and CLIP-Edited over ChordEdit, and improves at least four of five saved metrics. Examples were visually reviewed and chosen for visible content and diversity. They are not a random or representative subset. Full benchmark means are included on the page. No overall superiority, independent human evaluation, or exact leaf-count accuracy is claimed.

Local audit and full source/image provenance: `D:/BoyangDeng/ImageEditing/tmp/searchchord_website_20261012/asset_validation.json`. Absolute workspace paths are not included in the public JSON.

The manuscript is the current research draft; no conference acceptance or author identities are invented. When ready for a public author version, update authors and citation using the actual author list.
