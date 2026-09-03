/* ============================================================
   PSYCHSYNC UI COMPONENTS - Complete Component Library
   Import into TeleportHQ, Anima, or convert to Figma
   ============================================================ */

import React from 'react';

/* ===== BUTTON COMPONENTS ===== */

export const Button = ({
  variant = 'primary',
  size = 'md',
  children,
  disabled = false,
  ...props
}) => {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 500,
    borderRadius: '8px',
    transition: 'all 200ms ease',
    cursor: disabled ? 'not-allowed' : 'pointer',
    border: 'none',
    outline: 'none',
  };

  const sizes = {
    xs: { padding: '8px 12px', height: '32px', fontSize: '12px' },
    sm: { padding: '10px 14px', height: '40px', fontSize: '14px' },
    md: { padding: '12px 16px', height: '48px', fontSize: '16px' },
    lg: { padding: '16px 20px', height: '56px', fontSize: '16px' },
    xl: { padding: '20px 24px', height: '64px', fontSize: '18px' },
  };

  const variants = {
    primary: {
      backgroundColor: '#6366F1',
      color: '#FFFFFF',
      boxShadow: '0 4px 6px rgba(99, 102, 241, 0.2)',
      '&:hover': { backgroundColor: '#4F46E5', transform: 'translateY(-1px)' },
      '&:active': { backgroundColor: '#4338CA', transform: 'translateY(0)' },
    },
    secondary: {
      backgroundColor: 'transparent',
      color: '#6366F1',
      border: '2px solid #6366F1',
      '&:hover': { backgroundColor: '#EEF2FF' },
    },
    danger: {
      backgroundColor: '#EF4444',
      color: '#FFFFFF',
      '&:hover': { backgroundColor: '#DC2626' },
    },
    ghost: {
      backgroundColor: 'transparent',
      color: '#525252',
      '&:hover': { backgroundColor: '#F5F5F5' },
    },
  };

  return (
    <button
      style={{
        ...baseStyles,
        ...sizes[size],
        ...variants[variant],
        opacity: disabled ? 0.5 : 1,
      }}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

/* ===== CARD COMPONENT ===== */

export const Card = ({
  variant = 'default',
  children,
  className = '',
  ...props
}) => {
  const baseStyles = {
    borderRadius: variant === 'elevated' ? '16px' : '12px',
    padding: variant === 'elevated' ? '32px' : '24px',
    backgroundColor: '#FFFFFF',
    transition: 'all 200ms ease',
  };

  const variants = {
    default: {
      border: '1px solid #E5E5E5',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    },
    elevated: {
      border: 'none',
      boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1)',
    },
    interactive: {
      border: '1px solid #E5E5E5',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      cursor: 'pointer',
      '&:hover': {
        boxShadow: '0 20px 25px rgba(0, 0, 0, 0.1)',
        transform: 'translateY(-2px)',
      },
    },
  };

  return (
    <div
      className={className}
      style={{
        ...baseStyles,
        ...variants[variant],
      }}
      {...props}
    >
      {children}
    </div>
  );
};

/* ===== INPUT COMPONENT ===== */

export const Input = ({
  type = 'text',
  placeholder = '',
  error = false,
  disabled = false,
  ...props
}) => {
  return (
    <input
      type={type}
      placeholder={placeholder}
      disabled={disabled}
      style={{
        width: '100%',
        height: '48px',
        padding: '12px 16px',
        fontSize: '16px',
        color: '#171717',
        backgroundColor: '#FFFFFF',
        border: `2px solid ${error ? '#EF4444' : '#E5E5E5'}`,
        borderRadius: '8px',
        outline: 'none',
        transition: 'all 200ms ease',
        opacity: disabled ? 0.5 : 1,
        '&::placeholder': {
          color: '#A3A3A3',
        },
        '&:focus': {
          borderColor: '#6366F1',
          boxShadow: '0 0 0 4px rgba(99, 102, 241, 0.1)',
        },
      }}
      {...props}
    />
  );
};

/* ===== BADGE COMPONENT ===== */

export const Badge = ({
  variant = 'primary',
  children,
  ...props
}) => {
  const variants = {
    primary: { backgroundColor: '#EEF2FF', color: '#4338CA' },
    success: { backgroundColor: '#DCFCE7', color: '#15803D' },
    warning: { backgroundColor: '#FEF3C7', color: '#B45309' },
    danger: { backgroundColor: '#FEE2E2', color: '#B91C1C' },
    neutral: { backgroundColor: '#F5F5F5', color: '#404040' },
  };

  return (
    <span
      style={{
        display: 'inline-block',
        padding: '4px 12px',
        fontSize: '12px',
        fontWeight: 500,
        borderRadius: '9999px',
        ...variants[variant],
      }}
      {...props}
    >
      {children}
    </span>
  );
};

/* ===== ALERT COMPONENT ===== */

export const Alert = ({
  variant = 'info',
  title,
  children,
  ...props
}) => {
  const variants = {
    success: {
      backgroundColor: '#F0FDF4',
      borderLeft: '4px solid #22C55E',
      icon: '✓',
      iconColor: '#16A34A',
    },
    warning: {
      backgroundColor: '#FFFBEB',
      borderLeft: '4px solid #F59E0B',
      icon: '⚠',
      iconColor: '#D97706',
    },
    danger: {
      backgroundColor: '#FEF2F2',
      borderLeft: '4px solid #EF4444',
      icon: '✕',
      iconColor: '#DC2626',
    },
    info: {
      backgroundColor: '#EFF6FF',
      borderLeft: '4px solid #3B82F6',
      icon: 'ℹ',
      iconColor: '#2563EB',
    },
  };

  const config = variants[variant];

  return (
    <div
      style={{
        padding: '16px',
        borderRadius: '8px',
        backgroundColor: config.backgroundColor,
        borderLeft: config.borderLeft,
        display: 'flex',
        gap: '12px',
        alignItems: 'flex-start',
      }}
      {...props}
    >
      <span style={{ fontSize: '24px', color: config.iconColor }}>
        {config.icon}
      </span>
      <div style={{ flex: 1 }}>
        {title && (
          <div style={{ fontWeight: 600, marginBottom: '4px', fontSize: '16px' }}>
            {title}
          </div>
        )}
        <div style={{ fontSize: '16px', opacity: 0.9 }}>
          {children}
        </div>
      </div>
    </div>
  );
};

/* ===== PROGRESS BAR ===== */

export const ProgressBar = ({
  value = 0,
  max = 100,
  color = '#6366F1',
  ...props
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div
      style={{
        width: '100%',
        height: '8px',
        backgroundColor: '#E5E5E5',
        borderRadius: '9999px',
        overflow: 'hidden',
      }}
      {...props}
    >
      <div
        style={{
          width: `${percentage}%`,
          height: '100%',
          backgroundColor: color,
          borderRadius: '9999px',
          transition: 'width 300ms ease',
        }}
      />
    </div>
  );
};

/* ===== SIDEBAR COMPONENT ===== */

export const Sidebar = ({
  collapsed = false,
  activeItem = 'dashboard',
  onNavigate,
  ...props
}) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'teams', label: 'Teams', icon: '👥' },
    { id: 'toxic-behavior', label: 'Toxic Behavior', icon: '🛡️' },
    { id: 'burnout', label: 'Burnout Prevention', icon: '🔥' },
    { id: 'anonymous-feedback', label: 'Anonymous Feedback', icon: '🔒' },
    { id: 'behavioral-analytics', label: 'Behavioral Analytics', icon: '🧠' },
    { id: 'multi-framework', label: 'Multi-Framework', icon: '🧩' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <div
      style={{
        width: collapsed ? '80px' : '280px',
        height: '100vh',
        backgroundColor: '#FFFFFF',
        borderRight: '1px solid #E5E5E5',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 200ms ease',
      }}
      {...props}
    >
      {/* Logo Area */}
      <div style={{ height: '64px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid #E5E5E5' }}>
        <span style={{ fontSize: '24px', fontWeight: 'bold' }}>
          {collapsed ? '🧠' : 'PsychSync'}
        </span>
      </div>

      {/* Navigation Menu */}
      <div style={{ flex: 1, padding: '16px 8px' }}>
        {menuItems.map((item) => (
          <div
            key={item.id}
            onClick={() => onNavigate?.(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: collapsed ? '0' : '12px',
              padding: '12px',
              marginBottom: '4px',
              borderRadius: '8px',
              cursor: 'pointer',
              backgroundColor: activeItem === item.id ? '#EEF2FF' : 'transparent',
              color: activeItem === item.id ? '#4338CA' : '#525252',
              fontSize: '16px',
              fontWeight: 500,
              transition: 'all 150ms ease',
              justifyContent: collapsed ? 'center' : 'flex-start',
            }}
          >
            <span style={{ fontSize: '24px' }}>{item.icon}</span>
            {!collapsed && <span>{item.label}</span>}
          </div>
        ))}
      </div>

      {/* User Profile */}
      <div style={{ height: '80px', borderTop: '1px solid #E5E5E5', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', padding: '0 16px' }}>
        <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: '#6366F1', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>
          {collapsed ? '' : 'JD'}
        </div>
        {!collapsed && (
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#171717' }}>John Doe</div>
            <div style={{ fontSize: '12px', color: '#737373' }}>Admin</div>
          </div>
        )}
      </div>
    </div>
  );
};

/* ===== TOP BAR COMPONENT ===== */

export const TopBar = ({
  title = 'Dashboard',
  user = { name: 'John Doe', avatar: null },
  ...props
}) => {
  return (
    <div
      style={{
        height: '64px',
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid #E5E5E5',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
      }}
      {...props}
    >
      {/* Search Bar */}
      <div style={{ flex: 1, maxWidth: '320px' }}>
        <input
          type="text"
          placeholder="Search..."
          style={{
            width: '100%',
            height: '40px',
            padding: '0 16px',
            border: '1px solid #E5E5E5',
            borderRadius: '8px',
            fontSize: '14px',
          }}
        />
      </div>

      {/* Right Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <button style={{ width: '40px', height: '40px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '20px' }}>
          🔔
        </button>
        <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: '#6366F1', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>
          {user.name.charAt(0)}
        </div>
      </div>
    </div>
  );
};

/* ===== STAT CARD ===== */

export const StatCard = ({
  title,
  value,
  change,
  trend = 'up',
  icon,
  color = '#6366F1',
  ...props
}) => {
  return (
    <Card {...props}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div>
          <div style={{ fontSize: '14px', color: '#737373', marginBottom: '8px' }}>{title}</div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: '#171717' }}>{value}</div>
        </div>
        <div style={{ width: '48px', height: '48px', borderRadius: '12px', backgroundColor: `${color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px' }}>
          {icon}
        </div>
      </div>
      {change && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '14px' }}>
          <span style={{ color: trend === 'up' ? '#22C55E' : '#EF4444' }}>
            {trend === 'up' ? '↑' : '↓'}
          </span>
          <span style={{ color: trend === 'up' ? '#15803D' : '#B91C1C', fontWeight: 500 }}>
            {change}
          </span>
          <span style={{ color: '#737373' }}>from last month</span>
        </div>
      )}
    </Card>
  );
};

/* ===== DASHBOARD PAGE ===== */

export const DashboardPage = () => {
  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#FAFAFA' }}>
      <Sidebar activeItem="dashboard" />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <TopBar title="Dashboard" />

        <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
          {/* Page Header */}
          <div style={{ marginBottom: '32px' }}>
            <h1 style={{ fontSize: '36px', fontWeight: 700, color: '#171717', marginBottom: '8px' }}>
              Dashboard
            </h1>
            <p style={{ fontSize: '16px', color: '#525252' }}>
              Welcome back, John! Here's your team's wellness overview.
            </p>
          </div>

          {/* Stats Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginBottom: '32px' }}>
            <StatCard
              title="Total Assessments"
              value="247"
              change="+12.5%"
              trend="up"
              icon="📝"
              color="#6366F1"
            />
            <StatCard
              title="Team Members"
              value="48"
              change="+3"
              trend="up"
              icon="👥"
              color="#22C55E"
            />
            <StatCard
              title="Avg Wellness Score"
              value="7.8/10"
              change="+0.5"
              trend="up"
              icon="💚"
              color="#F59E0B"
            />
            <StatCard
              title="At Risk"
              value="5"
              change="-2"
              trend="down"
              icon="⚠️"
              color="#EF4444"
            />
          </div>

          {/* Charts Section */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
            <Card variant="elevated">
              <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: '#171717' }}>
                Wellness Trends
              </h3>
              <div style={{ height: '300px', backgroundColor: '#F5F5F5', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                [Chart Placeholder]
              </div>
            </Card>

            <Card variant="elevated">
              <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: '#171717' }}>
                Team Distribution
              </h3>
              <div style={{ height: '300px', backgroundColor: '#F5F5F5', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                [Chart Placeholder]
              </div>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

/* ===== BURNOUT PREVENTION PAGE ===== */

export const BurnoutPreventionPage = () => {
  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#FAFAFA' }}>
      <Sidebar activeItem="burnout" />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <TopBar title="Burnout Prevention" />

        <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
          {/* Critical Alert */}
          <Alert variant="danger" title="Critical Burnout Risk Detected" style={{ marginBottom: '24px' }}>
            Your burnout risk score indicates critical levels of stress. Immediate intervention required.
            Please contact HR or your manager within 24 hours.
          </Alert>

          {/* Page Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '32px' }}>🔥</span>
              <h1 style={{ fontSize: '36px', fontWeight: 700, color: '#171717', margin: 0 }}>
                Burnout Prevention & Prediction
              </h1>
            </div>
            <Button>Run Analysis</Button>
          </div>

          {/* Risk Score Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', marginBottom: '32px' }}>
            <Card variant="elevated">
              <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '24px', color: '#171717' }}>
                Overall Burnout Risk
              </h3>
              <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                <div style={{ fontSize: '72px', fontWeight: 700, color: '#EF4444', marginBottom: '8px' }}>78/100</div>
                <Badge variant="danger">HIGH RISK</Badge>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '14px', color: '#737373', marginBottom: '4px' }}>7-Day Probability</div>
                  <div style={{ fontSize: '24px', fontWeight: 600, color: '#171717' }}>23%</div>
                </div>
                <div>
                  <div style={{ fontSize: '14px', color: '#737373', marginBottom: '4px' }}>90-Day Turnover</div>
                  <div style={{ fontSize: '24px', fontWeight: 600, color: '#EF4444' }}>82%</div>
                </div>
              </div>
            </Card>

            <Card variant="elevated">
              <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '24px', color: '#171717' }}>
                Risk Stage
              </h3>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '36px', fontWeight: 600, color: '#F59E0B', marginBottom: '8px' }}>Exhaustion</div>
                <ProgressBar value={78} color="#F59E0B" />
              </div>
            </Card>
          </div>

          {/* Early Indicators */}
          <Card variant="elevated" style={{ marginBottom: '32px' }}>
            <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: '#171717' }}>
              Early Warning Indicators
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
              {[
                '4 consecutive weeks of 60+ hours',
                'Sent emails at 2 AM on 8 occasions',
                'Cancelled 3/4 scheduled 1:1s',
                'Vocabulary diversity dropped 34%',
                'Zero PTO days used in 6 months',
              ].map((indicator, i) => (
                <div key={i} style={{ padding: '12px', backgroundColor: '#FEF2F2', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: '#EF4444', fontSize: '20px' }}>✗</span>
                  <span style={{ fontSize: '14px', color: '#B91C1C' }}>{indicator}</span>
                </div>
              ))}
            </div>
          </Card>
        </main>
      </div>
    </div>
  );
};

/* ===== ANONYMOUS FEEDBACK PAGE ===== */

export const AnonymousFeedbackPage = () => {
  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#FAFAFA' }}>
      <Sidebar activeItem="anonymous-feedback" />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <TopBar title="Anonymous Feedback" />

        <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            {/* Privacy Guarantee */}
            <Alert variant="success" style={{ marginBottom: '32px' }}>
              <div style={{ fontSize: '16px', fontWeight: 600 }}>
                🔒 100% Anonymous
              </div>
              <div style={{ fontSize: '14px', marginTop: '8px' }}>
                Your identity will never be revealed. We do not track IP addresses, require accounts, or store any identifying information.
              </div>
            </Alert>

            {/* Page Header */}
            <div style={{ textAlign: 'center', marginBottom: '32px' }}>
              <span style={{ fontSize: '48px' }}>🔒</span>
              <h1 style={{ fontSize: '36px', fontWeight: 700, color: '#171717', marginBottom: '8px' }}>
                Anonymous Feedback System
              </h1>
              <p style={{ fontSize: '16px', color: '#525252' }}>
                A safe, confidential way to report workplace concerns
              </p>
            </div>

            {/* Feedback Form */}
            <Card variant="elevated">
              <div style={{ display: 'flex', gap: '24px', marginBottom: '24px' }}>
                <button style={{ flex: 1, padding: '12px', border: '2px solid #6366F1', borderRadius: '8px', backgroundColor: '#EEF2FF', color: '#4338CA', fontWeight: 600, fontSize: '16px' }}>
                  Submit Feedback
                </button>
                <button style={{ flex: 1, padding: '12px', border: '2px solid #E5E5E5', borderRadius: '8px', backgroundColor: 'transparent', color: '#525252', fontWeight: 500, fontSize: '16px' }}>
                  Check Status
                </button>
              </div>

              <form style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: '#171717' }}>
                    Feedback Category *
                  </label>
                  <select style={{ width: '100%', height: '48px', padding: '0 16px', fontSize: '16px', border: '2px solid #E5E5E5', borderRadius: '8px', backgroundColor: '#FFFFFF' }}>
                    <option>Select category...</option>
                    <option>Toxic Behavior</option>
                    <option>Workplace Harassment</option>
                    <option>Bullying</option>
                    <option>Discrimination</option>
                    <option>Safety Concern</option>
                    <option>Other</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: '#171717' }}>
                    Severity Level *
                  </label>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    {['Low', 'Medium', 'High', 'Critical'].map((level) => (
                      <label key={level} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px', padding: '12px', border: '2px solid #E5E5E5', borderRadius: '8px', cursor: 'pointer' }}>
                        <input type="radio" name="severity" style={{ width: '20px', height: '20px' }} />
                        <span style={{ fontSize: '14px', fontWeight: 500 }}>{level}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: '#171717' }}>
                    Description *
                  </label>
                  <textarea
                    placeholder="Please describe the incident or concern in detail..."
                    rows={6}
                    style={{ width: '100%', padding: '12px', fontSize: '16px', border: '2px solid #E5E5E5', borderRadius: '8px', resize: 'vertical', fontFamily: 'inherit' }}
                  />
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#737373' }}>
                    Minimum 10 characters, maximum 5000 characters
                  </div>
                </div>

                <Button size="lg" style={{ width: '100%' }}>
                  Submit Anonymous Feedback
                </Button>
              </form>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

/* ===== MULTI-FRAMEWORK SYNTHESIS PAGE ===== */

export const MultiFrameworkSynthesisPage = () => {
  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#FAFAFA' }}>
      <Sidebar activeItem="multi-framework" />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <TopBar title="Multi-Framework Synthesis" />

        <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
          {/* Page Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '32px' }}>🧩</span>
              <h1 style={{ fontSize: '36px', fontWeight: 700, color: '#171717', margin: 0 }}>
                Multi-Framework Synthesis
              </h1>
            </div>
            <Button>Run Synthesis</Button>
          </div>

          {/* Framework Overview */}
          <div style={{ marginBottom: '32px' }}>
            <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: '#171717' }}>
              Completed Assessments
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
              {[
                { name: 'Big Five', done: true },
                { name: 'MBTI', done: true },
                { name: 'Enneagram', done: true },
                { name: 'DISC', done: true },
                { name: 'Predictive Index', done: false },
                { name: 'StrengthsFinder', done: false },
                { name: 'Social Styles', done: false },
              ].map((fw) => (
                <Card key={fw.name} style={{ padding: '16px', border: `2px solid ${fw.done ? '#22C55E' : '#F59E0B'}` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>{fw.done ? '✅' : '⏳'}</span>
                    <span style={{ fontSize: '14px', fontWeight: 600, color: '#171717' }}>{fw.name}</span>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Synthesis Results */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
            <Card variant="elevated">
              <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: '#171717' }}>
                Synthesis Confidence
              </h3>
              <div style={{ textAlign: 'center', padding: '32px 0' }}>
                <div style={{ fontSize: '64px', fontWeight: 700, color: '#8B5CF6', marginBottom: '8px' }}>87%</div>
                <Badge variant="primary">High Confidence</Badge>
              </div>
            </Card>

            <Card variant="elevated">
              <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: '#171717' }}>
                Contradictions Resolved
              </h3>
              <div style={{ textAlign: 'center', padding: '32px 0' }}>
                <div style={{ fontSize: '64px', fontWeight: 700, color: '#F59E0B', marginBottom: '8px' }}>2</div>
                <div style={{ fontSize: '14px', color: '#737373' }}>Framework disagreements</div>
              </div>
            </Card>
          </div>

          {/* Unified Traits */}
          <Card variant="elevated" style={{ marginTop: '24px' }}>
            <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '24px', color: '#171717' }}>
              Unified Personality Traits
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              {[
                { trait: 'Openness', value: 78 },
                { trait: 'Conscientiousness', value: 82 },
                { trait: 'Extraversion', value: 52 },
                { trait: 'Agreeableness', value: 72 },
                { trait: 'Neuroticism', value: 35 },
                { trait: 'Analytical Thinking', value: 91 },
              ].map((item) => (
                <div key={item.trait} style={{ padding: '12px', backgroundColor: '#F5F5F5', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '14px', color: '#525252' }}>{item.trait}</span>
                    <span style={{ fontSize: '14px', fontWeight: 600, color: '#171717' }}>{item.value}%</span>
                  </div>
                  <ProgressBar value={item.value} color="#8B5CF6" />
                </div>
              ))}
            </div>
          </Card>
        </main>
      </div>
    </div>
  );
};

/* ===== EXPORT ALL COMPONENTS ===== */

export default {
  Button,
  Card,
  Input,
  Badge,
  Alert,
  ProgressBar,
  Sidebar,
  TopBar,
  StatCard,
  DashboardPage,
  BurnoutPreventionPage,
  AnonymousFeedbackPage,
  MultiFrameworkSynthesisPage,
};
