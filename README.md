# Myanmar Tipitaka — Native Android V2.3.7.7

**Release type: Offline 45-volume catalog / Approved-only Reader (NOT full-text).**

- 20 navigable native Android screens with dark teal and gold styling.
- 45/45 Myanmar/English volume index offline (Thai MCU edition: Vinaya 8, Sutta 25, Abhidhamma 12).
- SQLite read-only catalog in app assets; opens list, book details and reader without internet.
- Native reader supports approved-only Pali passages, Myanmar translations, and explanations when legitimately imported.
- Current catalog seed has **0 Pali passages, 0 approved Myanmar translations, 0 approved explanations**; no full-text claim.
- Find, bookmark, font adjustment and notes UI. Canonical paragraph crosswalk not yet verified.
- Never label AI-generated or unreviewed passages as approved.

## Build APK

Actions → **Build Myanmar Tipitaka V2.3.7.7 APK** → Run workflow (or push to main). The workflow regenerates `app/src/main/assets/tipitaka_verified_seed.sqlite` from `data/tipitaka_seed.sqlite.gz.b64`, builds with Gradle 8.9 + Android SDK 35, verifies debug signing and uploads `Myanmar-Tipitaka-V2.3.7.7-debug-APK` containing `app-debug.apk`.

The source seed derives from the verified-mapping content pack and contains only metadata, not licensed Tipitaka full texts. The app is an **installable testing build**, not a complete 45-book offline reader. Content must be licensed and reviewed before publication.
