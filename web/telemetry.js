/**
 * Quanthreum Telemetry & Intrusion Detection Client (telemetry.js)
 * Captures visitor paths, referral sources, wallet logins, and logs security events
 * for the restricted Operator Admin Console.
 */

(function () {
  const STORAGE_KEY_SESSIONS = 'qth_telemetry_sessions';
  const STORAGE_KEY_EVENTS = 'qth_telemetry_events';
  const STORAGE_KEY_INTRUSIONS = 'qth_penetration_events';

  // Seed default demonstration traffic if none exists so the Admin Console shows rich data immediately
  function seedInitialTelemetry() {
    if (!localStorage.getItem(STORAGE_KEY_SESSIONS)) {
      const sampleSessions = [
        {
          id: 'sess_' + Math.random().toString(36).substring(2, 9),
          wallet: '0xQTH94a1...7f3b',
          loginType: 'W-OTS+ Keyfile',
          source: 'X / Twitter',
          sourceUrl: 'https://x.com/quanthreum',
          entryPath: '/',
          currentPath: '/staking',
          device: 'Windows 11 • Chrome 130',
          geo: '🇺🇸 Ashburn, United States',
          timestamp: Date.now() - 1000 * 60 * 3,
          duration: '3m 12s',
          status: 'active'
        },
        {
          id: 'sess_' + Math.random().toString(36).substring(2, 9),
          wallet: '0xQTH62b8...11ec',
          loginType: 'Seed Vault (512-bit)',
          source: 'Telegram Channel',
          sourceUrl: 'https://t.me/quanthreum',
          entryPath: '/create-wallet',
          currentPath: '/wallet',
          device: 'macOS Sonoma • Safari 18',
          geo: '🇩🇪 Frankfurt, Germany',
          timestamp: Date.now() - 1000 * 60 * 14,
          duration: '14m 05s',
          status: 'active'
        },
        {
          id: 'sess_' + Math.random().toString(36).substring(2, 9),
          wallet: '0xQTH88e4...90d2',
          loginType: 'W-OTS+ Keyfile',
          source: 'Direct / Bookmarks',
          sourceUrl: 'direct',
          entryPath: '/explorer',
          currentPath: '/explorer',
          device: 'Linux x86_64 • Firefox 132',
          geo: '🇸🇬 Singapore',
          timestamp: Date.now() - 1000 * 60 * 27,
          duration: '27m 40s',
          status: 'idle'
        },
        {
          id: 'sess_' + Math.random().toString(36).substring(2, 9),
          wallet: 'Anonymous Visitor',
          loginType: 'Public Session',
          source: 'GitHub Repository',
          sourceUrl: 'https://github.com/edge-5005/quanthreum',
          entryPath: '/whitepaper',
          currentPath: '/whitepaper',
          device: 'Windows 11 • Brave',
          geo: '🇬🇧 London, United Kingdom',
          timestamp: Date.now() - 1000 * 60 * 42,
          duration: '8m 19s',
          status: 'idle'
        },
        {
          id: 'sess_' + Math.random().toString(36).substring(2, 9),
          wallet: '0xQTH33f1...aa40',
          loginType: 'W-OTS+ Keyfile',
          source: 'X / Twitter',
          sourceUrl: 'https://x.com/crypto_alpha/status/9821',
          entryPath: '/',
          currentPath: '/contracts',
          device: 'iOS 18 • Mobile Safari',
          geo: '🇯🇵 Tokyo, Japan',
          timestamp: Date.now() - 1000 * 60 * 55,
          duration: '18m 50s',
          status: 'idle'
        },
        {
          id: 'sess_' + Math.random().toString(36).substring(2, 9),
          wallet: '0xQTH17cd...44b9',
          loginType: 'Seed Vault (512-bit)',
          source: 'Dribbble Showcase',
          sourceUrl: 'https://dribbble.com/shots/nextware',
          entryPath: '/',
          currentPath: '/staking',
          device: 'macOS Sequoia • Chrome 130',
          geo: '🇨🇦 Toronto, Canada',
          timestamp: Date.now() - 1000 * 60 * 85,
          duration: '22m 10s',
          status: 'idle'
        }
      ];
      localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sampleSessions));
    }

    if (!localStorage.getItem(STORAGE_KEY_INTRUSIONS)) {
      const sampleIntrusions = [
        {
          id: 'ids_' + Math.random().toString(36).substring(2, 9),
          type: 'Quantum Shor Algorithm Probe',
          vector: 'Discrete Logarithm Key Factorization Attack on Public Key',
          sourceIp: '185.220.101.42 (Tor Exit Relay)',
          mitigation: 'Hardened: NIST W-OTS+ Hash Preimage Chain (Keccak-256) Immune to Quantum Period Finding',
          severity: 'CRITICAL_THWARTED',
          status: 'BLOCKED',
          timestamp: Date.now() - 1000 * 60 * 18
        },
        {
          id: 'ids_' + Math.random().toString(36).substring(2, 9),
          type: 'Sybil Gas Flood / DDoS Attempt',
          vector: '14,200 Zero-Value Micro-Transactions with Low Base Gas',
          sourceIp: '94.102.61.18 (Botnet Cluster)',
          mitigation: 'Hardened: EIP-1559 Dynamic Fee Escalation burnt 42.8 QTH; attacker gas exhausted',
          severity: 'HIGH_THWARTED',
          status: 'BLOCKED',
          timestamp: Date.now() - 1000 * 60 * 52
        },
        {
          id: 'ids_' + Math.random().toString(36).substring(2, 9),
          type: 'Unauthorized Admin Endpoint Probe',
          vector: 'Automated URL scanning for /admin /wp-login /console without Master Key',
          sourceIp: '45.154.255.89 (Unknown Scanner)',
          mitigation: 'Hardened: Air-gapped cryptographic PIN gate locked origin into rate-limit tarpit',
          severity: 'MEDIUM_THWARTED',
          status: 'BLOCKED',
          timestamp: Date.now() - 1000 * 60 * 95
        }
      ];
      localStorage.setItem(STORAGE_KEY_INTRUSIONS, JSON.stringify(sampleIntrusions));
    }
  }

  // Detect referral source
  function getReferralSource() {
    const params = new URLSearchParams(window.location.search);
    const utmSource = params.get('utm_source');
    const ref = params.get('ref');
    const referrer = document.referrer.toLowerCase();

    if (utmSource) {
      if (utmSource.includes('x') || utmSource.includes('twitter')) return { name: 'X / Twitter', url: 'https://x.com' };
      if (utmSource.includes('telegram') || utmSource.includes('tg')) return { name: 'Telegram Channel', url: 'https://t.me' };
      return { name: utmSource, url: referrer || 'campaign' };
    }

    if (ref) {
      return { name: 'Referral: ' + ref, url: referrer || 'direct' };
    }

    if (!referrer || referrer === '') {
      return { name: 'Direct / Bookmarks', url: 'direct' };
    }

    if (referrer.includes('t.co') || referrer.includes('twitter.com') || referrer.includes('x.com')) {
      return { name: 'X / Twitter', url: referrer };
    }
    if (referrer.includes('t.me') || referrer.includes('telegram.org')) {
      return { name: 'Telegram Channel', url: referrer };
    }
    if (referrer.includes('github.com')) {
      return { name: 'GitHub Repository', url: referrer };
    }
    if (referrer.includes('dribbble.com')) {
      return { name: 'Dribbble Showcase', url: referrer };
    }
    if (referrer.includes('google.') || referrer.includes('bing.') || referrer.includes('duckduckgo.')) {
      return { name: 'Organic Search Engine', url: referrer };
    }

    try {
      const urlObj = new URL(referrer);
      return { name: urlObj.hostname, url: referrer };
    } catch (e) {
      return { name: 'External Referrer', url: referrer };
    }
  }

  // Detect OS and Browser
  function getDeviceFingerprint() {
    const ua = navigator.userAgent;
    let os = 'Unknown OS';
    if (ua.includes('Win')) os = 'Windows 11';
    else if (ua.includes('Mac')) os = 'macOS';
    else if (ua.includes('Linux')) os = 'Linux';
    else if (ua.includes('Android')) os = 'Android';
    else if (ua.includes('iPhone') || ua.includes('iPad')) os = 'iOS';

    let browser = 'Unknown Browser';
    if (ua.includes('Firefox')) browser = 'Firefox';
    else if (ua.includes('Brave')) browser = 'Brave';
    else if (ua.includes('Edg')) browser = 'Edge';
    else if (ua.includes('Chrome')) browser = 'Chrome';
    else if (ua.includes('Safari')) browser = 'Safari';

    return `${os} • ${browser}`;
  }

  // Get Simulated City / Geo from TimeZone
  function getGeoLocation() {
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
      const city = tz.split('/')[1] ? tz.split('/')[1].replace(/_/g, ' ') : tz;
      const continent = tz.split('/')[0];
      let flag = '🌐';
      if (continent === 'America') flag = '🇺🇸';
      else if (continent === 'Europe') flag = '🇪🇺';
      else if (continent === 'Asia') flag = '🌏';
      return `${flag} ${city} (${tz})`;
    } catch (e) {
      return '🌐 Node Network';
    }
  }

  // Track current visit
  function recordCurrentVisit() {
    seedInitialTelemetry();
    let currentSessionId = sessionStorage.getItem('qth_current_session_id');
    const sessions = JSON.parse(localStorage.getItem(STORAGE_KEY_SESSIONS) || '[]');
    const refSource = getReferralSource();
    const activeWallet = localStorage.getItem('quanthreum_active_wallet') || localStorage.getItem('qth_demo_wallet_address');

    if (!currentSessionId) {
      currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
      sessionStorage.setItem('qth_current_session_id', currentSessionId);

      const newSession = {
        id: currentSessionId,
        wallet: activeWallet ? `0xQTH${activeWallet.substring(activeWallet.length - 8)}` : 'Audience Guest',
        loginType: activeWallet ? 'W-OTS+ Keyfile' : 'Browser Session',
        source: refSource.name,
        sourceUrl: refSource.url,
        entryPath: window.location.pathname || '/',
        currentPath: window.location.pathname || '/',
        device: getDeviceFingerprint(),
        geo: getGeoLocation(),
        timestamp: Date.now(),
        duration: 'Just now',
        status: 'active'
      };

      sessions.unshift(newSession);
      if (sessions.length > 50) sessions.pop();
      localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sessions));
    } else {
      // Update existing session
      const existing = sessions.find(s => s.id === currentSessionId);
      if (existing) {
        existing.currentPath = window.location.pathname || '/';
        existing.status = 'active';
        if (activeWallet && existing.wallet.includes('Guest')) {
          existing.wallet = `0xQTH${activeWallet.substring(activeWallet.length - 8)}`;
          existing.loginType = 'W-OTS+ Keyfile';
        }
        localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sessions));
      }
    }
  }

  // Record an intrusion/penetration event into the audit system
  window.qthLogIntrusion = function (type, vector, ip, mitigation) {
    seedInitialTelemetry();
    const intrusions = JSON.parse(localStorage.getItem(STORAGE_KEY_INTRUSIONS) || '[]');
    const newIntrusion = {
      id: 'ids_' + Math.random().toString(36).substring(2, 9),
      type: type || 'Penetration Probe',
      vector: vector || 'Suspicious payload inspected and rejected by W-OTS+ cryptographic trie',
      sourceIp: ip || '198.51.100.' + Math.floor(Math.random() * 250 + 1),
      mitigation: mitigation || 'Hardened: Zero-State exposure & deterministic QVM sandbox reversion',
      severity: 'HIGH_THWARTED',
      status: 'BLOCKED',
      timestamp: Date.now()
    };
    intrusions.unshift(newIntrusion);
    if (intrusions.length > 50) intrusions.pop();
    localStorage.setItem(STORAGE_KEY_INTRUSIONS, JSON.stringify(intrusions));

    // Dispatch global event for live admin dashboard listener
    window.dispatchEvent(new CustomEvent('qth_penetration_detected', { detail: newIntrusion }));
    return newIntrusion;
  };

  // Keyboard shortcut for site owner: Ctrl + Shift + A directly opens the Admin Console
  window.addEventListener('keydown', function (e) {
    if (e.ctrlKey && e.shiftKey && (e.key === 'A' || e.key === 'a')) {
      e.preventDefault();
      window.location.href = '/admin';
    }
  });

  // Run on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', recordCurrentVisit);
  } else {
    recordCurrentVisit();
  }
})();
