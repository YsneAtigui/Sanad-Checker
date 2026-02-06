---
name: frontend-design
description: Design patterns and guidelines for the Sanad AEO Auditor dashboard. Covers Arabic RTL layout, severity-based color coding, audit result visualization, and responsive design for e-commerce AEO reporting interfaces. Use when designing UI mockups, implementing dashboard components, or creating audit visualization interfaces.
---

# Frontend Design for Sanad AEO Auditor

Design guidelines for building the Sanad audit dashboard with Arabic RTL support and AEO-specific visualizations.

## Design Principles

### 1. Arabic-First Design

**RTL (Right-to-Left) Layout:**
- Default direction: RTL for Arabic interface
- LTR for code snippets, URLs, technical data
- Bidirectional text support for mixed content

**Typography:**
- Primary: **Noto Sans Arabic** or **Cairo** (web-safe Arabic fonts)
- Code/Technical: **Fira Code** or **JetBrains Mono**
- Sizes: 16px base, 20px headings (larger for Arabic readability)

**Language Switching:**
```jsx
// Toggle between Arabic and English
<LanguageToggle>
  <button onClick={() => setLang('ar')} dir="rtl">العربية</button>
  <button onClick={() => setLang('en')} dir="ltr">English</button>
</LanguageToggle>
```

### 2. Severity-Based Color System

Use consistent colors across the dashboard:

```css
:root {
  /* Severity colors */
  --severity-critical: #DC2626;  /* Red 600 */
  --severity-high: #EA580C;      /* Orange 600 */
  --severity-medium: #F59E0B;    /* Amber 500 */
  --severity-low: #3B82F6;       /* Blue 500 */
  --severity-none: #10B981;      /* Green 500 */
  
  /* Background variants */
  --bg-critical: #FEE2E2;
  --bg-high: #FFEDD5;
  --bg-medium: #FEF3C7;
  --bg-low: #DBEAFE;
  --bg-none: #D1FAE5;
  
  /* Arabic-friendly neutrals */
  --text-primary: #1F2937;
  --text-secondary: #6B7280;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F9FAFB;
}
```

### 3. Score Visualization

**Overall AEO Score (0-100):**

```jsx
// Circular progress with Arabic numerals
<ScoreCircle score={67}>
  <svg viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="45" 
      stroke-dasharray={`${score * 2.83} 283`}
      className={getScoreColor(score)} />
  </svg>
  <div className="score-text">
    <span className="score-number">{toArabicNumerals(67)}</span>
    <span className="score-label">نقاط</span>
  </div>
</ScoreCircle>

// Color based on score
function getScoreColor(score) {
  if (score >= 80) return 'text-green-500';
  if (score >= 60) return 'text-amber-500';
  return 'text-red-500';
}

// Convert to Arabic-Indic numerals
function toArabicNumerals(num) {
  return num.toString().replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
}
```

## Core Components

### Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  Header: Logo, Language Toggle, Settings            │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────┐  ┌───────────────────────────┐ │
│  │                │  │                            │ │
│  │  URL Submit    │  │   Recent Audits            │ │
│  │  Form          │  │   (Cards with status)      │ │
│  │                │  │                            │ │
│  └────────────────┘  └───────────────────────────┘ │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  Audit Results (when loaded)                 │  │
│  │  ┌────────┐  ┌──────────────────────────┐   │  │
│  │  │ Score  │  │  Issues by Severity      │   │  │
│  │  │ Circle │  │  🔴 Critical: 2          │   │  │
│  │  │  67%   │  │  ⚠️  High: 3             │   │  │
│  │  └────────┘  │  🟡 Medium: 5            │   │  │
│  │              └──────────────────────────┘   │  │
│  │                                              │  │
│  │  Detailed Findings (Expandable sections)    │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 1. URL Submission Form

```jsx
<AuditSubmitForm>
  <input
    type="url"
    placeholder="https://store.salla.sa/product/..."
    dir="ltr"  // URLs are always LTR
    className="w-full px-4 py-3 text-lg border rounded-lg"
  />
  
  <button className="bg-blue-600 text-white px-6 py-3 rounded-lg">
    {lang === 'ar' ? 'بدء التدقيق' : 'Start Audit'}
  </button>
  
  {/* Options */}
  <label>
    <input type="checkbox" checked={options.bilingual} />
    <span>{lang === 'ar' ? 'فحص ثنائي اللغة' : 'Bilingual Check'}</span>
  </label>
</AuditSubmitForm>
```

### 2. Audit Status Card

```jsx
<AuditCard status={audit.status}>
  <div className="flex justify-between items-start">
    <div>
      <h3 className="text-lg font-semibold truncate" dir="ltr">
        {audit.url}
      </h3>
      <p className="text-sm text-gray-500">
        {formatDate(audit.created_at, lang)}
      </p>
    </div>
    
    {/* Status badge */}
    <StatusBadge status={audit.status}>
      {getStatusText(audit.status, lang)}
    </StatusBadge>
  </div>
  
  {/* Progress bar for in-progress audits */}
  {audit.status === 'in_progress' && (
    <ProgressBar progress={audit.progress} />
  )}
  
  {/* Score for completed audits */}
  {audit.status === 'completed' && (
    <div className="flex items-center gap-2 mt-2">
      <ScoreBadge score={audit.overall_score} />
      <SeverityChips counts={audit.severity_counts} />
    </div>
  )}
</AuditCard>
```

### 3. Issues List

```jsx
<IssuesSection>
  {/* Critical Issues */}
  {issues.critical.length > 0 && (
    <IssueGroup severity="critical">
      <h3 className="flex items-center gap-2 text-red-600">
        <AlertCircle className="w-5 h-5" />
        <span>{lang === 'ar' ? 'مشاكل حرجة' : 'Critical Issues'}</span>
        <Badge>{issues.critical.length}</Badge>
      </h3>
      
      {issues.critical.map(issue => (
        <IssueCard key={issue.id} severity="critical">
          <div className="flex items-start gap-3">
            <IssueIcon type={issue.type} />
            <div className="flex-1">
              <h4 className="font-semibold">{issue.title}</h4>
              <p className="text-sm text-gray-600">{issue.description}</p>
              
              {/* Recommendation */}
              {issue.recommendation && (
                <div className="mt-2 p-2 bg-blue-50 rounded border-l-4 border-blue-500">
                  <p className="text-sm">
                    <strong>{lang === 'ar' ? 'الحل:' : 'Fix:'}</strong>
                    {issue.recommendation}
                  </p>
                </div>
              )}
            </div>
          </div>
        </IssueCard>
      ))}
    </IssueGroup>
  )}
  
  {/* Repeat for high, medium, low */}
</IssuesSection>
```

### 4. Protocol Checklist

```jsx
<ProtocolChecklist results={audit.protocol_results}>
  <CheckItem 
    status={results.llms_txt.status}
    label={lang === 'ar' ? 'ملف llms.txt' : 'llms.txt file'}
    icon={<FileText />}
  />
  
  <CheckItem
    status={results.agent_card.status}
    label={lang === 'ar' ? 'بطاقة الوكيل A2A' : 'A2A Agent Card'}
    icon={<Shield />}
  />
  
  <CheckItem
    status={results.robots_txt.ai_agents_blocked ? 'blocked' : 'allowed'}
    label={lang === 'ar' ? 'وصول الوكلاء الذكيين' : 'AI Agent Access'}
    icon={<Bot />}
  />
</ProtocolChecklist>

// Status icons
const statusIcons = {
  found: <CheckCircle className="text-green-500" />,
  missing: <XCircle className="text-red-500" />,
  malformed: <AlertTriangle className="text-amber-500" />
};
```

### 5. Report Export

```jsx
<ExportButtons audit={audit}>
  <button onClick={() => exportMarkdown(audit.id)}>
    <Download /> {lang === 'ar' ? 'تحميل Markdown' : 'Download Markdown'}
  </button>
  
  <button onClick={() => exportJSON(audit.id)}>
    <Code /> {lang === 'ar' ? 'تحميل JSON' : 'Download JSON'}
  </button>
  
  <button onClick={() => copyShareLink(audit.id)}>
    <Share2 /> {lang === 'ar' ? 'مشاركة الرابط' : 'Share Link'}
  </button>
</ExportButtons>
```

## Responsive Design

### Breakpoints

```css
/* Mobile-first approach */
@media (min-width: 640px) {  /* sm */
  /* Tablet layout */
}

@media (min-width: 1024px) { /* lg */
  /* Desktop layout: 2-column grid */
  .dashboard-grid {
    grid-template-columns: 1fr 2fr;
  }
}

@media (min-width: 1280px) { /* xl */
  /* Wide desktop: 3-column for issue cards */
}
```

### Mobile Optimizations

- Stack cards vertically
- Collapsible issue sections
- Bottom sheet for detailed views
- Touch-friendly buttons (min 44px height)

## Accessibility

### WCAG 2.1 AA Compliance

```jsx
// Proper ARIA labels for Arabic
<button 
  aria-label={lang === 'ar' ? 'بدء تدقيق جديد' : 'Start new audit'}
  aria-busy={isLoading}
>
  {/* ... */}
</button>

// Keyboard navigation
<nav role="navigation" aria-label={lang === 'ar' ? 'التنقل الرئيسي' : 'Main navigation'}>
  {/* Tab order should follow RTL in Arabic */}
</nav>

// Screen reader announcements
<div role="status" aria-live="polite" aria-atomic="true">
  {lang === 'ar' ? 'اكتمل التدقيق' : 'Audit completed'}
</div>
```

### Color Contrast

- All severity colors meet WCAG AA contrast (4.5:1)
- Use icons + colors (not color alone)
- Test with tools: axe DevTools, WAVE

## Technology Stack

**Recommended:**
- **React + TypeScript** for type safety
- **TailwindCSS** for RTL support (`dir="rtl"`)
- **Radix UI** or **Headless UI** for accessible components
- **Recharts** or **Victory** for score visualizations
- **React Query** for API state management

**RTL Support:**
```js
// tailwind.config.js
module.exports = {
  plugins: [
    require('tailwindcss-rtl'),
  ],
};
```

## Sample Page Structure

```jsx
import { useTranslation } from 'react-i18next';

function AuditDashboard() {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === 'ar';
  
  return (
    <div dir={isRTL ? 'rtl' : 'ltr'} className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-1">
            <AuditSubmitForm />
            <RecentAudits audits={recentAudits} />
          </aside>
          
          {/* Main content */}
          <section className="lg:col-span-2">
            {selectedAudit && (
              <>
                <AuditHeader audit={selectedAudit} />
                <ScoreOverview audit={selectedAudit} />
                <IssuesList issues={selectedAudit.issues} />
                <DetailedFindings audit={selectedAudit} />
              </>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
```

## Visual Design Assets

**Icons:**
- Use **Lucide Icons** (24px default)
- Issue type icons: 🚫 blocked, 📄 missing file, 🔍 schema error, 💰 price mismatch

**Illustrations:**
- Empty state: "No audits yet" illustration
- Loading state: Animated audit progress
- Error state: Connection error illustration

## Critical Rules

- Always set `dir="rtl"` for Arabic content
- Use `dir="ltr"` for URLs, code, and technical content
- Test with Arabic-Indic numerals (٠-٩) option
- Severity colors must be consistent across all components
- Mobile: collapsible sections for better performance
- Export reports maintain RTL formatting in Markdown
