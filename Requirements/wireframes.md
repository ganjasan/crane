# UI Wireframes — OSINT Platform MVP

## 1. Login

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    🔍 OSINT Platform                    │
│              Collaborative Evidence Collection           │
│                                                         │
│            ┌─────────────────────────────┐              │
│            │ Email                       │              │
│            └─────────────────────────────┘              │
│            ┌─────────────────────────────┐              │
│            │ Password                    │              │
│            └─────────────────────────────┘              │
│                                                         │
│            ┌─────────────────────────────┐              │
│            │         Sign In             │              │
│            └─────────────────────────────┘              │
│                                                         │
│            Have an invite link? Click it.               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 2. Organization Selector (`/`)

```
┌─────────────────────────────────────────────────────────┐
│ OSINT Platform                          artem@email.com │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Your Organizations                                     │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ ICF / CACN                                        │  │
│  │ International Crane Foundation                     │  │
│  │ 2 projects · 8 members                    Enter → │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Forest Watch Central Asia                         │  │
│  │ Timber trade monitoring                           │  │
│  │ 1 project · 3 members                    Enter → │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │
│  │         + Create New Organization                 │  │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 3. Organization Dashboard (`/icf/`)

```
┌─────────────────────────────────────────────────────────┐
│ OSINT Platform    ICF / CACN ▾         artem@email.com  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Projects                              [+ New Project]  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Bird Trade — Central & South Asia                 │  │
│  │ 142 incidents · 5 volunteers · 68% coverage       │  │
│  │ Last activity: 2 hours ago                Open → │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Bird Trade — East Asian Flyway                    │  │
│  │ 0 incidents · 0 volunteers · setup pending        │  │
│  │ Created: today                          Setup → │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Members (8)                     [Invite Member]        │
│                                                         │
│  Artem Konuchov          owner                          │
│  Ella Mikusheva          admin                          │
│  Ramesh Kumar            admin                          │
│  intern1@example.com     member      (invite pending)   │
│  ...                                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 4. Project Dashboard — Coordinator View (`/icf/bird-trade-csa/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ OSINT Platform   ICF ▾  Bird Trade CSA ▾                artem ▾        │
├────────────┬────────────────────────────────────────────────────────────┤
│            │                                                            │
│ Dashboard  │  Bird Trade — Central & South Asia                        │
│ ─────────  │                                                            │
│ Incidents  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│ Keywords   │  │ 142      │ │ 7        │ │ 5        │ │ 68%          │ │
│ Coverage   │  │ total    │ │ this wk  │ │ active   │ │ coverage     │ │
│ Settings   │  │ incidents│ │ incidents│ │ volnteers│ │ score        │ │
│            │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │
│ ─────────  │                                                            │
│ Team       │  ┌─ Needs Attention ──────────────────────────────────┐   │
│            │  │                                                     │   │
│            │  │  ⚠ 5 incidents awaiting review          [Review →] │   │
│            │  │  ⚠ 3 keywords pending approval          [Review →] │   │
│            │  │  ⚠ 2 incidents with incomplete data     [Fix →]    │   │
│            │  │                                                     │   │
│            │  └─────────────────────────────────────────────────────┘   │
│            │                                                            │
│            │  ┌─ Coverage Gaps (worst) ────────────────────────────┐   │
│            │  │                                                     │   │
│            │  │  ██ Telegram × Tajik × sale      never searched    │   │
│            │  │  ██ OLX × Uzbek × purchase       45 days ago       │   │
│            │  │  ██ VK × Kazakh × hunting        38 days ago       │   │
│            │  │  ░░ Facebook × Urdu × sale        12 days ago      │   │
│            │  │                           [Full Coverage Matrix →]  │   │
│            │  └─────────────────────────────────────────────────────┘   │
│            │                                                            │
│            │  ┌─ Recent Incidents ─────────────────────────────────┐   │
│            │  │                                                     │   │
│            │  │  BTCA-142  Facebook  Demoiselle Crane   submitted  │   │
│            │  │            Ella · 2 hours ago                       │   │
│            │  │  BTCA-141  Telegram  Sarus Crane        reviewed   │   │
│            │  │            intern3 · 5 hours ago                    │   │
│            │  │  BTCA-140  OLX       Bar-headed Goose   reviewed   │   │
│            │  │            intern1 · yesterday                      │   │
│            │  │  ...                          [All Incidents →]     │   │
│            │  └─────────────────────────────────────────────────────┘   │
│            │                                                            │
└────────────┴────────────────────────────────────────────────────────────┘
```

## 5. Incident List (`/icf/bird-trade-csa/incidents/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ OSINT Platform   ICF ▾  Bird Trade CSA ▾                artem ▾        │
├────────────┬────────────────────────────────────────────────────────────┤
│            │                                                            │
│ Dashboard  │  Incidents (142)              [+ New Incident] [Export ↓]  │
│ ─────────  │                                                            │
│ Incidents ←│  ┌─ Filters ──────────────────────────────────────────┐   │
│ Keywords   │  │ Platform [All    ▾] Status [All    ▾]              │   │
│ Coverage   │  │ Language [All    ▾] Confidence [All ▾]             │   │
│ Settings   │  │ Date from [____] to [____]  Search [____________]  │   │
│            │  └────────────────────────────────────────────────────┘   │
│            │                                                            │
│            │  ┌────┬──────────┬────────────┬──────────┬─────┬───────┐ │
│            │  │ ID │ Platform │ Species    │ Volunter │ Date│Status │ │
│            │  ├────┼──────────┼────────────┼──────────┼─────┼───────┤ │
│            │  │142 │ Facebook │ Demoiselle │ Ella     │ 4/13│⬤ subm │ │
│            │  │141 │ Telegram │ Sarus      │ intern3  │ 4/13│✓ revd │ │
│            │  │140 │ OLX      │ Bar-headed │ intern1  │ 4/12│✓ revd │ │
│            │  │139 │ Facebook │ Eurasian   │ intern2  │ 4/12│✓ revd │ │
│            │  │138 │ VK       │ Ruddy Shel.│ intern1  │ 4/11│⚑ flag │ │
│            │  │137 │ Telegram │ Demoiselle │ Ella     │ 4/11│✓ revd │ │
│            │  │136 │ Facebook │ Demoiselle │ intern3  │ 4/10│✓ revd │ │
│            │  │... │          │            │          │     │       │ │
│            │  └────┴──────────┴────────────┴──────────┴─────┴───────┘ │
│            │                                                            │
│            │  ← 1 2 3 4 5 ... 15 →                                     │
│            │                                                            │
└────────────┴────────────────────────────────────────────────────────────┘
```

## 6. Incident Detail (`/icf/bird-trade-csa/incidents/142/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ OSINT Platform   ICF ▾  Bird Trade CSA ▾                artem ▾        │
├────────────┬────────────────────────────────────────────────────────────┤
│            │                                                            │
│ Dashboard  │  Incident BTCA-142                 Status: ⬤ submitted    │
│ ─────────  │                                    [Review ✓] [Flag ⚑]    │
│ Incidents ←│                                                            │
│ Keywords   │  ┌─ Evidence ──────────────┬─ Details ──────────────────┐ │
│ Coverage   │  │                         │                             │ │
│ Settings   │  │  ┌───────────────────┐  │  Platform:   Facebook      │ │
│            │  │  │                   │  │  URL:         fb.com/p/... │ │
│            │  │  │                   │  │  Post date:   2026-04-13   │ │
│            │  │  │   [Screenshot]    │  │  Collected:   2026-04-13   │ │
│            │  │  │                   │  │  Collected by: Ella        │ │
│            │  │  │   Demoiselle      │  │  Language:    Hindi        │ │
│            │  │  │   Crane Pair      │  │  Confidence:  High        │ │
│            │  │  │   Rs 35,000       │  │                             │ │
│            │  │  │                   │  │  ─── Bird Trade Fields ─── │ │
│            │  │  └───────────────────┘  │                             │ │
│            │  │                         │  Species:     Demoiselle   │ │
│            │  │  Keywords matched:      │  Scientific:  A. virgo     │ │
│            │  │  • "crane for sale"     │  Trade term:  Koonj        │ │
│            │  │  • "demoiselle crane"   │  Group:       Crane        │ │
│            │  │                         │  Purpose:     Pet          │ │
│            │  │                         │  Quantity:    2 (pair)     │ │
│            │  │                         │  Price:       Rs 35,000   │ │
│            │  │                         │  Seller:      Individual   │ │
│            │  │                         │  Trade type:  Sale         │ │
│            │  │                         │  Verification: High        │ │
│            │  └─────────────────────────┴─────────────────────────────┘ │
│            │                                                            │
│            │  Notes: "Seller advertising a breeding pair. Active       │
│            │  account with multiple bird posts. Comments show           │
│            │  negotiation on price."                                    │
│            │                                                            │
│            │  ⚠ Potential duplicate: similar to BTCA-098       [View]  │
│            │                                                            │
│            │  [Edit]                                      [← Back]     │
│            │                                                            │
└────────────┴────────────────────────────────────────────────────────────┘
```

## 7. Annotation Form — New Incident (`/icf/bird-trade-csa/incidents/new/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ OSINT Platform   ICF ▾  Bird Trade CSA ▾                artem ▾        │
├────────────┬────────────────────────────────────────────────────────────┤
│            │                                                            │
│ Dashboard  │  New Incident                                              │
│ ─────────  │                                                            │
│ Incidents  │  ─── Core Fields ──────────────────────────────────────── │
│ Keywords   │                                                            │
│ Coverage   │  Platform *        ┌─────────────────────────────────┐    │
│ Settings   │                    │ Select platform...            ▾ │    │
│            │                    └─────────────────────────────────┘    │
│            │  URL *             ┌─────────────────────────────────┐    │
│            │                    │ https://                         │    │
│            │                    └─────────────────────────────────┘    │
│            │  Screenshot *      ┌─────────────────────────────────┐    │
│            │                    │ 📎 Choose file or drag & drop   │    │
│            │                    └─────────────────────────────────┘    │
│            │  Date of post      ┌─────────────────────────────────┐    │
│            │                    │ yyyy-mm-dd                       │    │
│            │                    └─────────────────────────────────┘    │
│            │  Location          ┌─────────────────────────────────┐    │
│            │  mentioned         │                                 │    │
│            │                    └─────────────────────────────────┘    │
│            │  Probable          ┌─────────────────────────────────┐    │
│            │  location          │                                 │    │
│            │                    └─────────────────────────────────┘    │
│            │  Language *        ┌─────────────────────────────────┐    │
│            │                    │ Select language...            ▾ │    │
│            │                    └─────────────────────────────────┘    │
│            │  Keywords          ┌─────────────────────────────────┐    │
│            │  matched           │ Search keywords...     ▾ multi │    │
│            │                    └─────────────────────────────────┘    │
│            │  Confidence *      ○ High  ○ Medium  ○ Low               │
│            │                                                            │
│            │  ─── Bird Trade Fields ────────────────────────────────── │
│            │                                                            │
│            │  Species *         ┌─────────────────────────────────┐    │
│            │                    │ Search species...             ▾ │    │
│            │                    └─────────────────────────────────┘    │
│            │  Trade term        ┌─────────────────────────────────┐    │
│            │                    │ Local name used in post         │    │
│            │                    └─────────────────────────────────┘    │
│            │  Purpose *         ┌─────────────────────────────────┐    │
│            │                    │ Select purpose...             ▾ │    │
│            │                    └─────────────────────────────────┘    │
│            │  Quantity          ┌──────────┐                          │
│            │                    │          │                          │
│            │                    └──────────┘                          │
│            │  Price             ┌─────────────────────────────────┐    │
│            │                    │                                 │    │
│            │                    └─────────────────────────────────┘    │
│            │  Trade type *      ┌─────────────────────────────────┐    │
│            │                    │ Select type...               ▾ │    │
│            │                    └─────────────────────────────────┘    │
│            │                                                            │
│            │  ─── Notes ────────────────────────────────────────────── │
│            │  ┌─────────────────────────────────────────────────────┐  │
│            │  │                                                     │  │
│            │  │                                                     │  │
│            │  └─────────────────────────────────────────────────────┘  │
│            │                                                            │
│            │           [Save Draft]              [Submit for Review]    │
│            │                                                            │
└────────────┴────────────────────────────────────────────────────────────┘
```

## 8. Keyword Bank (`/icf/bird-trade-csa/keywords/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ OSINT Platform   ICF ▾  Bird Trade CSA ▾                artem ▾        │
├────────────┬────────────────────────────────────────────────────────────┤
│            │                                                            │
│ Dashboard  │  Keyword Bank (487)         [+ Add Keyword] [Import CSV]  │
│ ─────────  │                                                            │
│ Incidents  │  ┌─ Filters ──────────────────────────────────────────┐   │
│ Keywords ← │  │ Language [All ▾] Category [All ▾] Status [All ▾]  │   │
│ Coverage   │  │ Search [________________________]                  │   │
│ Settings   │  └────────────────────────────────────────────────────┘   │
│            │                                                            │
│            │  ┌──────────────────────┬────┬──────┬────────┬─────────┐ │
│            │  │ Term                 │Lang│Categ.│Matches │ Status  │ │
│            │  ├──────────────────────┼────┼──────┼────────┼─────────┤ │
│            │  │ crane for sale       │ EN │ sale │   23   │ ✓ active│ │
│            │  │ demoiselle crane     │ EN │ sp.  │   18   │ ✓ active│ │
│            │  │ koonj bechna hai     │ UR │ sale │   12   │ ✓ active│ │
│            │  │ журавль продам       │ RU │ sale │    9   │ ✓ active│ │
│            │  │ турна сатылат        │ KY │ sale │    7   │ ✓ active│ │
│            │  │ crane pair price     │ EN │price │    5   │ ✓ active│ │
│            │  │ পাখি বিক্রি         │ BN │ sale │    —   │ ⏳ cand.│ │
│            │  │ bird market lahore   │ EN │market│    4   │ ✓ active│ │
│            │  │ ...                  │    │      │        │         │ │
│            │  └──────────────────────┴────┴──────┴────────┴─────────┘ │
│            │                                                            │
│            │  ⏳ 3 keywords pending approval              [Review →]   │
│            │                                                            │
└────────────┴────────────────────────────────────────────────────────────┘
```

## 9. Coverage Matrix (`/icf/bird-trade-csa/coverage/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ OSINT Platform   ICF ▾  Bird Trade CSA ▾                artem ▾        │
├────────────┬────────────────────────────────────────────────────────────┤
│            │                                                            │
│ Dashboard  │  Search Coverage Matrix              [Log My Search]      │
│ ─────────  │                                                            │
│ Incidents  │  Click a cell to see details. Red = needs attention.      │
│ Keywords   │                                                            │
│ Coverage ← │       │ sale │ purch│ hunt │ transp│ slang│ sp-spec│      │
│ Settings   │  ─────┼──────┼──────┼──────┼───────┼──────┼────────┤      │
│            │  FB   │      │      │      │       │      │        │      │
│            │   EN  │ 🟢2d │ 🟢5d │ 🟡15d│ 🟡22d │ 🟢3d │ 🟢1d  │      │
│            │   HI  │ 🟢4d │ 🟡12d│ 🟡20d│ 🔴45d │ 🟡14d│ 🟢6d  │      │
│            │   UR  │ 🟢3d │ 🟢7d │ 🟡18d│ 🔴60d │ 🟡10d│ 🟢5d  │      │
│            │   KY  │ 🟡9d │ 🔴35d│ 🔴40d│ 🔴nev │ 🔴32d│ 🟡11d │      │
│            │   RU  │ 🟢2d │ 🟢6d │ 🟡14d│ 🟡25d │ 🟢4d │ 🟢3d  │      │
│            │  ─────┼──────┼──────┼──────┼───────┼──────┼────────┤      │
│            │  TG   │      │      │      │       │      │        │      │
│            │   EN  │ 🟢1d │ 🟢3d │ 🟡10d│ 🟡20d │ 🟢2d │ 🟢1d  │      │
│            │   KY  │ 🟡8d │ 🔴nev│ 🔴nev│ 🔴nev │ 🔴nev│ 🔴nev │      │
│            │   TJ  │ 🔴nev│ 🔴nev│ 🔴nev│ 🔴nev │ 🔴nev│ 🔴nev │      │
│            │   RU  │ 🟢3d │ 🟡12d│ 🟡16d│ 🟡28d │ 🟢5d │ 🟢4d  │      │
│            │  ─────┼──────┼──────┼──────┼───────┼──────┼────────┤      │
│            │  OLX  │      │      │      │       │      │        │      │
│            │   KY  │ 🟡10d│ 🔴38d│ 🔴nev│ 🔴nev │ 🟡15d│ 🟡12d │      │
│            │   UZ  │ 🔴45d│ 🔴nev│ 🔴nev│ 🔴nev │ 🔴nev│ 🔴nev │      │
│            │  ─────┼──────┼──────┼──────┼───────┼──────┼────────┤      │
│            │  VK   │      │      │      │       │      │        │      │
│            │   RU  │ 🟢4d │ 🟢7d │ 🟡18d│ 🟡22d │ 🟢6d │ 🟢5d  │      │
│            │   KZ  │ 🔴38d│ 🔴nev│ 🔴nev│ 🔴nev │ 🔴nev│ 🔴nev │      │
│            │  ...  │      │      │      │       │      │        │      │
│            │                                                            │
│            │  🟢 < 7 days  🟡 8-30 days  🔴 > 30 days / never         │
│            │                                                            │
│            │  ─── Volunteer Activity ──────────────────────────────     │
│            │  ┌──────────────┬────────┬──────────┬──────────────┐      │
│            │  │ Volunteer    │Sessions│ Findings │ Last active  │      │
│            │  ├──────────────┼────────┼──────────┼──────────────┤      │
│            │  │ Ella         │   34   │    28    │ 2 hours ago  │      │
│            │  │ intern1      │   22   │    15    │ yesterday    │      │
│            │  │ intern3      │   18   │    11    │ 5 hours ago  │      │
│            │  │ intern2      │   12   │     6    │ 3 days ago   │      │
│            │  │ intern4      │    3   │     1    │ 12 days ago  │      │
│            │  └──────────────┴────────┴──────────┴──────────────┘      │
│            │                                                            │
└────────────┴────────────────────────────────────────────────────────────┘
```

## 10. Log Search Form (compact, modal or inline)

```
┌──────────────────────────────────────────┐
│  Log Search Session                   ✕  │
│                                          │
│  Platform *   ┌──────────────────────┐   │
│               │ Telegram           ▾ │   │
│               └──────────────────────┘   │
│  Language *   ┌──────────────────────┐   │
│               │ Kyrgyz             ▾ │   │
│               └──────────────────────┘   │
│  Categories * ┌──────────────────────┐   │
│               │ ☑ sale               │   │
│               │ ☑ hunting            │   │
│               │ ☐ purchase           │   │
│               │ ☐ transport          │   │
│               │ ☐ slang              │   │
│               │ ☐ species-specific   │   │
│               └──────────────────────┘   │
│  Date         ┌──────────────────────┐   │
│               │ 2026-04-13           │   │
│               └──────────────────────┘   │
│  Duration     ┌──────────────────────┐   │
│  (minutes)    │ 30                   │   │
│               └──────────────────────┘   │
│  Incidents    ┌──────────────────────┐   │
│  found        │ 2                    │   │
│               └──────────────────────┘   │
│  Notes        ┌──────────────────────┐   │
│               │ Found 2 posts with   │   │
│               │ crane sale ads...    │   │
│               └──────────────────────┘   │
│                                          │
│           [Cancel]    [Log Search]       │
│                                          │
└──────────────────────────────────────────┘
```

## 11. Mobile — Annotation Form (360px)

```
┌──────────────────────────┐
│ ☰  Bird Trade CSA        │
├──────────────────────────┤
│                          │
│  New Incident            │
│                          │
│  Platform *              │
│  ┌────────────────────┐  │
│  │ Facebook          ▾│  │
│  └────────────────────┘  │
│                          │
│  URL *                   │
│  ┌────────────────────┐  │
│  │ https://fb.com/... │  │
│  └────────────────────┘  │
│                          │
│  Screenshot *            │
│  ┌────────────────────┐  │
│  │ 📷 Take photo or   │  │
│  │    choose file     │  │
│  └────────────────────┘  │
│                          │
│  Species *               │
│  ┌────────────────────┐  │
│  │ Demoiselle Crane  ▾│  │
│  └────────────────────┘  │
│                          │
│  Price                   │
│  ┌────────────────────┐  │
│  │ Rs 35,000          │  │
│  └────────────────────┘  │
│                          │
│  Trade type *            │
│  ┌────────────────────┐  │
│  │ Sale              ▾│  │
│  └────────────────────┘  │
│                          │
│  Confidence *            │
│  [High] [Medium] [Low]  │
│                          │
│  Notes                   │
│  ┌────────────────────┐  │
│  │                    │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │    Save Draft      │  │
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │  Submit for Review │  │
│  └────────────────────┘  │
│                          │
└──────────────────────────┘
```

## 12. Browser Extension Popup

```
┌────────────────────────────┐
│  OSINT Capture             │
│  ─────────────────────     │
│                            │
│  Project: Bird Trade CSA   │
│                            │
│  ┌──────────────────────┐  │
│  │                      │  │
│  │   📸 Capture This    │  │
│  │       Page           │  │
│  │                      │  │
│  └──────────────────────┘  │
│                            │
│  Detected: Facebook        │
│  URL: fb.com/post/456...   │
│                            │
│  ────────────────────      │
│  Last capture: 2 min ago   │
│  Total today: 3            │
│                            │
│  ⚙ Settings               │
└────────────────────────────┘
```
