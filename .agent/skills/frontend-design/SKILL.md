---
name: frontend-design
description: Design patterns and guidelines for the Sanad AEO Auditor platform. Modern light-mode SaaS design inspired by mobbin.com. Covers complete design system, component library, landing page, dashboard, and comprehensive audit report interfaces. English-only professional UI/UX specifications for e-commerce AEO auditing.
---

# Frontend Design for Sanad AEO Auditor

Complete design system and UI specifications for building a modern SaaS AEO auditing platform.

## Design System

### Color Palette (Light Mode)

```css
:root {
  /* Primary Colors */
  --primary-blue: #2563EB;
  --primary-hover: #1D4ED8;
  --bg-page: #F9FAFB;
  --bg-card: #FFFFFF;
  --border-light: #E5E7EB;
  
  /* Text Colors */
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --text-muted: #9CA3AF;
  
  /* Status Colors */
  --success: #10B981;
  --warning: #F59E0B;
  --error: #EF4444;
  --info: #3B82F6;
  
  /* Severity Colors (Audit-Specific) */
  --severity-critical: #DC2626;  /* Red */
  --severity-high: #F59E0B;      /* Orange */
  --severity-medium: #FBBF24;    /* Yellow */
  --severity-low: #10B981;       /* Green */
}
```

### Typography

```css
/* Font Stack */
font-family: Inter, system-ui, -apple-system, sans-serif;

/* Scale */
--text-h1: 36px / 44px;     /* Hero headlines */
--text-h2: 30px / 38px;     /* Section headers */
--text-h3: 24px / 32px;     /* Card titles */
--text-h4: 20px / 28px;     /* Subsections */
--text-body: 16px / 24px;   /* Body text */
--text-small: 14px / 20px;  /* Captions, labels */
--text-caption: 12px / 16px; /* Badges, tiny text */

/* Weights */
--weight-regular: 400;
--weight-medium: 500;
--weight-semibold: 600;
```

### Spacing System

Base unit: **16px (1rem)**

Scale: `4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px`

### Component Styles

#### Buttons

```css
/* Primary Button */
.btn-primary {
  background: var(--primary-blue);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 150ms;
}
.btn-primary:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

/* Secondary Button */
.btn-secondary {
  background: white;
  color: var(--primary-blue);
  border: 1px solid var(--primary-blue);
  padding: 12px 24px;
  border-radius: 8px;
}

/* Sizes */
.btn-sm { height: 32px; padding: 8px 16px; font-size: 14px; }
.btn-md { height: 40px; padding: 12px 24px; } /* Default */
.btn-lg { height: 48px; padding: 14px 32px; font-size: 18px; }
```

#### Cards

```css
.card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: box-shadow 200ms;
}
.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
```

#### Input Fields

```css
.input {
  height: 44px;
  padding: 12px 16px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  font-size: 16px;
  transition: all 150ms;
}
.input:focus {
  outline: none;
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
```

#### Badges

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.badge-critical { background: #FEE2E2; color: #991B1B; }
.badge-high { background: #FFEDD5; color: #9A3412; }
.badge-medium { background: #FEF3C7; color: #92400E; }
.badge-low { background: #D1FAE5; color: #065F46; }
.badge-success { background: #D1FAE5; color: #065F46; }
```

---

## Page Layouts

### 1. Marketing Landing Page

**Sections**:
1. Navigation (sticky)
2. Hero with URL input
3. Problem/Solution (2-column)
4. Features (6 audit cards)
5. Live demo carousel
6. Platform logos
7. Pricing tiers
8. Testimonials
9. FAQ accordion
10. Final CTA
11. Footer

**Hero Component**:
```jsx
<section className="hero">
  {/* Navigation */}
  <nav className="sticky top-0 bg-white border-b">
    <div className="container flex justify-between items-center py-4">
      <Logo />
      <MenuLinks>Features | Solutions | Pricing | Docs</MenuLinks>
      <AuthButtons>
        <button className="btn-ghost">Login</button>
        <button className="btn-primary">Start Free Trial</button>
      </AuthButtons>
    </div>
  </nav>

  {/* Hero Content */}
  <div className="container text-center py-24">
    <Badge className="mb-4">🚀 Now supporting 7 AI agents</Badge>
    <h1 className="text-5xl font-bold mb-4">
      Know Exactly How AI Sees Your Store
    </h1>
    <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
      Comprehensive Answer Engine Optimization audits for Arabic e-commerce.
      Get instant insights on AI visibility, protocol compliance, and content quality.
    </p>
    
    {/* CTA Input */}
    <div className="flex gap-2 max-w-2xl mx-auto">
      <input 
        type="url" 
        placeholder="https://your-store.com/product/..."
        className="flex-1 input-lg"
      />
      <button className="btn-primary btn-lg">
        Audit for Free →
      </button>
    </div>
    <p className="text-sm text-gray-500 mt-2">
      ✓ No credit card required
    </p>
  </div>
</section>
```

**Feature Cards (Grid)**:
```jsx
<section className="features py-16 bg-gray-50">
  <div className="container">
    <h2 className="text-3xl font-bold text-center mb-12">
      What We Audit
    </h2>
    
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Card 1: Protocol Compliance */}
      <FeatureCard
        icon="📋"
        title="Protocol Validation"
        checks={[
          "✓ llms.txt discovery file",
          "✓ Google A2A agent-card.json",
          "✓ robots.txt AI agent rules"
        ]}
        label="4 critical checks"
      />
      
      {/* Card 2: Schema Accuracy */}
      <FeatureCard
        icon="🏷️"
        title="JSON-LD Structure"
        checks={[
          "✓ Product schema validation",
          "✓ UCP 2026 compliance",
          "✓ Price & availability",
          "✓ Bilingual consistency"
        ]}
        label="23 data points"
      />
      
      {/* Repeat for 6 total cards */}
    </div>
  </div>
</section>
```

---

### 2. Authentication Pages

**Split-Screen Layout**:
```jsx
<div className="grid lg:grid-cols-2 min-h-screen">
  {/* Left: Branding */}
  <aside className="bg-gradient-to-br from-blue-600 to-blue-800 p-12 flex flex-col justify-center">
    <Logo className="text-white mb-8" />
    <img src="/dashboard-preview.png" alt="Dashboard" className="rounded-lg shadow-2xl" />
    <blockquote className="text-white text-xl mt-8">
      "Audit your first product in under 60 seconds"
    </blockquote>
  </aside>

  {/* Right: Form */}
  <main className="flex items-center justify-center p-8">
    <div className="w-full max-w-md">
      <h2 className="text-3xl font-bold mb-6">Welcome back</h2>
      
      <form className="space-y-4">
        <Input label="Email address" type="email" />
        <Input label="Password" type="password" showToggle />
        
        <div className="flex items-center justify-between">
          <Checkbox label="Remember me" />
          <Link href="/forgot-password">Forgot password?</Link>
        </div>
        
        <button className="btn-primary w-full">Sign In</button>
        
        <Divider>or</Divider>
        
        <button className="btn-secondary w-full">
          <GoogleIcon /> Continue with Google
        </button>
      </form>
      
      <p className="text-center mt-6 text-gray-600">
        Don't have an account? <Link href="/signup">Sign up</Link>
      </p>
    </div>
  </main>
</div>
```

---

### 3. Dashboard - Audit Interface

**Layout Structure**:
```jsx
<div className="flex h-screen bg-gray-50">
  {/* Sidebar */}
  <Sidebar className="w-64 bg-white border-r">
    <Logo />
    <Nav>
      <NavItem icon={<Home />} active>Dashboard</NavItem>
      <NavItem icon={<Plus />}>New Audit</NavItem>
      <NavItem icon={<List />}>Recent Audits</NavItem>
      <NavItem icon={<BarChart />}>Analytics</NavItem>
      <NavItem icon={<Settings />}>Settings</NavItem>
    </Nav>
  </Sidebar>

  {/* Main Content */}
  <main className="flex-1 overflow-auto">
    {/* Top Bar */}
    <header className="sticky top-0 bg-white border-b px-8 py-4 flex justify-between items-center">
      <Breadcrumb>Home / Dashboard</Breadcrumb>
      <UserMenu />
    </header>

    {/* Content */}
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">AEO Audit Dashboard</h1>
      
      {/* Stats Cards */}
      <StatsGrid />
      
      {/* New Audit Form */}
      <AuditInputCard />
      
      {/* Recent Audits Table */}
      <RecentAuditsTable />
    </div>
  </main>
</div>
```

**Audit Input Card** (Prominent):
```jsx
<Card className="mb-8 bg-white shadow-lg">
  <div className="flex items-center gap-4 mb-4">
    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
      <Search className="text-blue-600" />
    </div>
    <h3 className="text-xl font-semibold">Start New Audit</h3>
  </div>
  
  <div className="flex gap-3">
    <input
      type="url"
      placeholder="https://your-store.salla.sa/product/12345"
      className="flex-1 input-lg"
    />
    <button className="btn-primary btn-lg">
      Scan Now →
    </button>
  </div>
  
  <div className="mt-4 space-y-2">
    <Toggle label="Include bilingual analysis (AR + EN)" />
    <Toggle label="Deep content scoring with LLM" />
    <Toggle label="Compare with competitors" />
  </div>
  
  <p className="text-sm text-gray-500 mt-4">
    Estimated time: ~45 seconds
  </p>
</Card>
```

**Recent Audits Table**:
```jsx
<Card>
  <div className="flex justify-between items-center mb-4">
    <h3 className="text-xl font-semibold">Recent Audits</h3>
    <div className="flex gap-2">
      <Select options={['All Platforms', 'Salla', 'Zid', 'Shopify']} />
      <SearchInput placeholder="Search by URL" />
    </div>
  </div>

  <Table>
    <thead>
      <tr>
        <th>URL</th>
        <th>Platform</th>
        <th>Score</th>
        <th>Status</th>
        <th>Issues</th>
        <th>Date</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {audits.map(audit => (
        <tr key={audit.id} className="hover:bg-gray-50 cursor-pointer">
          <td>
            <div className="flex items-center gap-2">
              <img src={audit.favicon} className="w-4 h-4" />
              <span className="truncate">{audit.url}</span>
            </div>
          </td>
          <td>
            <Badge className="badge-platform">{audit.platform}</Badge>
          </td>
          <td>
            <ScoreCircle score={audit.score} size="sm" />
          </td>
          <td>
            <StatusBadge status={audit.status} />
          </td>
          <td>
            <IssueBadges counts={audit.issues} />
          </td>
          <td className="text-gray-500">{audit.date}</td>
          <td>
            <ActionButtons audit={audit} />
          </td>
        </tr>
      ))}
    </tbody>
  </Table>
</Card>
```

---

### 4. Comprehensive Report View

**Sticky Header**:
```jsx
<header className="sticky top-0 bg-white border-b shadow-sm z-10">
  <div className="container py-4 flex justify-between items-center">
    {/* Left: Back + URL */}
    <div>
      <button className="btn-ghost mb-2">← All Audits</button>
      <h1 className="text-lg font-semibold">{audit.url}</h1>
      <p className="text-sm text-gray-500">
        <PlatformBadge>{audit.platform}</PlatformBadge>
        <span className="mx-2">•</span>
        Audited {formatDate(audit.created_at)}
      </p>
    </div>

    {/* Center: Score */}
    <div className="text-center">
      <ScoreGauge score={78} size="lg" />
      <Badge className="badge-medium mt-2">Medium Risk</Badge>
    </div>

    {/* Right: Actions */}
    <div className="flex gap-2">
      <button className="btn-secondary">Export PDF</button>
      <button className="btn-primary">Re-scan</button>
      <ShareDropdown />
    </div>
  </div>
</header>
```

**Summary Cards Row**:
```jsx
<div className="grid grid-cols-4 gap-4 mb-8">
  <MetricCard
    icon="📋"
    title="Protocol Compliance"
    value="3/4 Passed"
    progress={75}
    status="1 missing file"
    color="blue"
  />
  <MetricCard
    icon="🏷️"
    title="Schema Validation"
    value="85% Complete"
    progress={85}
    status="3 UCP fields missing"
    color="green"
  />
  <MetricCard
    icon="🌐"
    title="Edge Visibility"
    value="5/7 Agents"
    progress={71}
    status="2 blocked by Cloudflare"
    color="yellow"
  />
  <MetricCard
    icon="✍️"
    title="Content Quality"
    value="72/100"
    progress={72}
    status="Some robotic patterns"
    color="yellow"
  />
</div>
```

**Tabbed Interface**:
```jsx
<Tabs defaultTab="overview">
  <TabList>
    <Tab>Overview</Tab>
    <Tab>Protocol Check</Tab>
    <Tab>Schema Analysis</Tab>
    <Tab>Edge Visibility</Tab>
    <Tab>Content Quality</Tab>
    <Tab>Recommendations</Tab>
  </TabList>

  {/* Overview Tab */}
  <TabPanel id="overview">
    <div className="grid lg:grid-cols-2 gap-6">
      {/* Left: Critical Issues */}
      <Card>
        <h3 className="text-xl font-semibold mb-4">
          Critical Issues (2)
        </h3>
        {criticalIssues.map(issue => (
          <IssueCard key={issue.id} severity="critical">
            <Badge className="badge-critical">Critical</Badge>
            <h4 className="font-semibold mt-2">{issue.title}</h4>
            <p className="text-sm text-gray-600">{issue.description}</p>
            <button className="btn-sm mt-2">View Details →</button>
          </IssueCard>
        ))}
      </Card>

      {/* Right: Severity Breakdown */}
      <Card>
        <h3 className="text-xl font-semibold mb-4">Severity Breakdown</h3>
        <DonutChart data={severityData} />
        <Legend>
          <Item color="red">Critical: 2</Item>
          <Item color="orange">High: 5</Item>
          <Item color="yellow">Medium: 8</Item>
          <Item color="green">Low: 3</Item>
        </Legend>
      </Card>
    </div>
  </TabPanel>

  {/* Protocol Check Tab */}
  <TabPanel id="protocol">
    <ProtocolCheckSection />
  </TabPanel>

  {/* Other tabs... */}
</Tabs>
```

**Protocol Check Details** (Expandable Cards):
```jsx
<div className="space-y-4">
  {/* llms.txt */}
  <ExpandableCard
    status="error"
    icon="✗"
    title="llms.txt - Not Found"
    badge="Critical"
  >
    <p className="text-gray-700 mb-4">
      The llms.txt file is missing. AI agents use this file to discover
      your products and understand your catalog.
    </p>
    
    <InfoGrid>
      <InfoItem label="Expected Location">/llms.txt</InfoItem>
      <InfoItem label="Status">404 Not Found</InfoItem>
      <InfoItem label="Impact">High - AI agents cannot autodiscover content</InfoItem>
    </InfoGrid>
    
    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
      <h5 className="font-semibold mb-2">What's Missing:</h5>
      <ul className="list-disc list-inside text-sm space-y-1">
        <li>H1 site title</li>
        <li>Blockquote summary</li>
        <li>Links to key products</li>
      </ul>
    </div>
    
    <div className="flex gap-2 mt-4">
      <button className="btn-primary">Generate Template</button>
      <button className="btn-secondary">View Documentation</button>
    </div>
  </ExpandableCard>

  {/* agent-card.json */}
  <ExpandableCard
    status="warning"
    icon="⚠️"
    title="agent-card.json - Incomplete"
    badge="Medium"
  >
    {/* Similar structure with validation details and code preview */}
  </ExpandableCard>

  {/* robots.txt */}
  <ExpandableCard
    status="success"
    icon="✓"
    title="robots.txt - Configured"
    badge="Passed"
  >
    {/* Success details */}
  </ExpandableCard>
</div>
```

---

## Specialized Components

### Score Gauge (Circular)

```jsx
function ScoreGauge({ score, size = 'md' }) {
  const sizes = {
    sm: { diameter: 60, strokeWidth: 6, fontSize: '16px' },
    md: { diameter: 100, strokeWidth: 8, fontSize: '24px' },
    lg: { diameter: 120, strokeWidth: 10, fontSize: '32px' }
  };
  
  const config = sizes[size];
  const radius = (config.diameter - config.strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  
  const getColor = (score) => {
    if (score >= 80) return '#10B981'; // Green
    if (score >= 60) return '#F59E0B'; // Yellow
    return '#EF4444'; // Red
  };
  
  return (
    <div className="relative inline-flex">
      <svg width={config.diameter} height={config.diameter}>
        {/* Background circle */}
        <circle
          cx={config.diameter / 2}
          cy={config.diameter / 2}
          r={radius}
          fill="none"
          stroke="#E5E7EB"
          strokeWidth={config.strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={config.diameter / 2}
          cy={config.diameter / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth={config.strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
          transform={`rotate(-90 ${config.diameter / 2} ${config.diameter / 2})`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-bold" style={{ fontSize: config.fontSize }}>
          {score}
        </span>
        <span className="text-gray-500 text-xs">/100</span>
      </div>
    </div>
  );
}
```

### Issue Severity Chips

```jsx
function IssueBadges({ counts }) {
  return (
    <div className="flex gap-1">
      {counts.critical > 0 && (
        <span className="inline-flex items-center gap-1 text-xs">
          <span className="w-2 h-2 rounded-full bg-red-500"></span>
          {counts.critical}
        </span>
      )}
      {counts.high > 0 && (
        <span className="inline-flex items-center gap-1 text-xs">
          <span className="w-2 h-2 rounded-full bg-orange-500"></span>
          {counts.high}
        </span>
      )}
      {counts.medium > 0 && (
        <span className="inline-flex items-center gap-1 text-xs">
          <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
          {counts.medium}
        </span>
      )}
      {counts.low > 0 && (
        <span className="inline-flex items-center gap-1 text-xs">
          <span className="w-2 h-2 rounded-full bg-green-500"></span>
          {counts.low}
        </span>
      )}
    </div>
  );
}
```

### Loading States

```jsx
// Skeleton Loader
function SkeletonCard() {
  return (
    <div className="animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>
  );
}

// Audit Progress Modal
function AuditProgressModal() {
  return (
    <Modal>
      <div className="text-center p-8">
        <Spinner className="w-16 h-16 text-blue-600 mb-4" />
        <h3 className="text-xl font-semibold mb-2">Auditing your product...</h3>
        <ProgressBar progress={progress} className="mb-4" />
        
        <div className="space-y-1 text-sm text-gray-600">
          <Step completed>Fetching page content</Step>
          <Step active>Checking protocols</Step>
          <Step>Validating schema</Step>
          <Step>Testing AI agents</Step>
          <Step>Analyzing content</Step>
        </div>
        
        <p className="text-sm text-gray-500 mt-4">
          ~30 seconds remaining
        </p>
      </div>
    </Modal>
  );
}
```

---

## Responsive Design

### Breakpoints
```css
/* Mobile: < 640px (stack everything) */
/* Tablet: 640px - 1024px (2-column grids) */
/* Desktop: 1024px - 1440px (3-4 column grids) */
/* Large: > 1440px (constrained max-width) */

@media (max-width: 640px) {
  .sidebar { display: none; }
  .mobile-menu { display: block; }
  .table { display: block; overflow-x: auto; }
}
```

---

## Accessibility Standards

- **WCAG 2.1 AA Compliance**
- Color contrast ratio: minimum 4.5:1
- Focus indicators: 2px blue outline
- ARIA labels on all interactive elements
- Keyboard navigation support
- Screen reader friendly

---

## Technology Recommendations

- **Framework**: React + TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui or Headless UI
- **Charts**: Recharts
- **Icons**: Heroicons or Lucide
- **Forms**: React Hook Form + Zod
- **Animation**: Framer Motion

---

## Critical Design Rules

1. **Consistency**: Use design tokens for all colors, spacing, typography
2. **Clarity**: Maximum information density without overwhelming
3. **Hierarchy**: Clear visual hierarchy in reports (score → issues → details)
4. **Performance**: Lazy load heavy components (charts, code viewers)
5. **Mobile**: Touch targets minimum 44px, collapsible sections
6. **Feedback**: Loading states for all async actions
7. **Export**: All reports downloadable as PDF/Markdown/JSON
