# SCOR Website

Static multilingual website project for SCOR heavy equipment, international shipping, logistics, products, content pages, contact, alfa administration interface, PWA installation support, and image optimization.

## Languages

- English: `/en/`
- Arabic: `/ar/`
- German: `/de/`
- Turkish: `/tr/`
- Admin interface: `/alfa/`

## Requirements

- Node.js 18+
- Python 3
- Optional for image optimization when adding original images: Pillow

Install the optional image optimizer dependency:

```bash
pip install -r requirements.txt
```

## Commands

```bash
npm run build
npm run preview
```

The generated static site is written to:

```text
site/
```

## Content

Main editable data is stored in:

```text
src/data/site-data.mjs
```

Generated responsive image metadata is stored in:

```text
src/data/generated-images.json
```

## Image Optimization

Put large original images in:

```text
src/assets/media/originals/
```

During build, optimized responsive derivatives are generated in:

```text
src/assets/media/generated/
```

The site can then use responsive image markup with WebP, width-based `srcset`, lazy loading, async decoding, and browser caching.

## PWA

The build generates:

- `manifest.webmanifest`
- language-specific manifests
- `sw.js`
- app icons under `assets/app/`

This allows the website and alfa interface to be installed as an app from supported browsers.

## Project Structure

```text
build.mjs                    Static site generator
package.json                 Project commands
requirements.txt             Optional Python dependency for image optimization
scripts/                     Build helper scripts
src/assets/                  Brand, app, and media assets
src/data/                    Website data
site/                        Generated static output
```
