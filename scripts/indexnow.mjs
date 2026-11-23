// Tells Bing (and the other IndexNow engines) about every page in the sitemap. Run from the repo root after a
// deploy that adds or changes pages: node scripts/indexnow.mjs. The key is the name of the <key>.txt file at the root.
import { readFileSync, readdirSync } from 'node:fs'

const HOST = 'georgeclinkscalesdev.com'
const keyFile = readdirSync('.').find(f => /^[0-9a-f]{32}\.txt$/.test(f))
if (!keyFile) throw new Error('No <32-hex-key>.txt file found at the repo root')
const key = keyFile.replace('.txt', '')
const urlList = [...readFileSync('sitemap.xml', 'utf8').matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1])
  .filter(u => new URL(u).host === HOST)

const res = await fetch('https://api.indexnow.org/indexnow', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8' },
  body: JSON.stringify({ host: HOST, key, keyLocation: `https://${HOST}/${keyFile}`, urlList }),
})
console.log(`IndexNow: ${res.status} for ${urlList.length} URLs`)
if (res.status !== 200 && res.status !== 202) process.exit(1)
