import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname, relative, posix } from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const siteRoot = join(projectRoot, 'site');

function walk(dir, out = []) {
  for (const item of readdirSync(dir)) {
    const full = join(dir, item);
    const st = statSync(full);
    if (st.isDirectory()) walk(full, out);
    else if (item.endsWith('.html')) out.push(full);
  }
  return out;
}

function toPosix(path) {
  return path.split('\\').join('/');
}

function targetForPublicPath(publicPath) {
  let p = publicPath.split('#')[0].split('?')[0];
  if (!p.startsWith('/')) return null;
  if (p === '/') return join(siteRoot, 'index.html');
  const raw = p.replace(/^\//, '');
  let target = join(siteRoot, raw);
  if (existsSync(target) && statSync(target).isDirectory()) target = join(target, 'index.html');
  else if (!posix.extname(raw)) target = join(target, 'index.html');
  return target;
}

function relFrom(htmlFile, target) {
  let rel = toPosix(relative(dirname(htmlFile), target));
  if (!rel.startsWith('.')) rel = './' + rel;
  return rel;
}

const languageRoots = ['/en', '/ar', '/de', '/tr'];

function rewritePublicUrl(htmlFile, value) {
  if (!languageRoots.some(prefix => value.startsWith(prefix)) && !value.startsWith('/assets')) return value;
  const hash = value.includes('#') ? '#' + value.split('#').slice(1).join('#') : '';
  const target = targetForPublicPath(value);
  if (!target) return value;
  return relFrom(htmlFile, target) + hash;
}

function rewriteSrcset(htmlFile, value) {
  return value.split(',').map(part => {
    const trimmed = part.trim();
    if (!trimmed) return trimmed;
    const pieces = trimmed.split(/\s+/);
    pieces[0] = rewritePublicUrl(htmlFile, pieces[0]);
    return pieces.join(' ');
  }).join(', ');
}

for (const htmlFile of walk(siteRoot)) {
  let html = readFileSync(htmlFile, 'utf8');
  html = html.replace(/(href|src)="(\/(?:en|ar|de|tr)[^"]*|\/assets[^"]*)"/g, (_, attr, value) => `${attr}="${rewritePublicUrl(htmlFile, value)}"`);
  html = html.replace(/srcset="([^"]+)"/g, (_, value) => `srcset="${rewriteSrcset(htmlFile, value)}"`);
  html = html.replace(/url=\/en\//g, 'url=en/index.html');
  html = html.replace(/"(\/assets\/catalogs\/[^"]+\.pdf)"/g, (_, value) => `"${rewritePublicUrl(htmlFile, value)}"`);
  writeFileSync(htmlFile, html);
}
