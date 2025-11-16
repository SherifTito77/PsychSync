// #/frontend/mobile_pwa.tsx
import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Users, Award, Bell, Settings, Menu, X, Search, Home, BarChart3 } from 'lucide-react';
const MobileNBAApp = () => {
  const [activeTab, setActiveTab] = useState('home');
  const [menuOpen, setMenuOpen] = useState(false);
  const [notifications, setNotifications] = useState(3);
  const [searchQuery, setSearchQuery] = useState('');
  const [isOnline, setIsOnline] = useState(true);
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  const topPlayers = [
    { id: 1, name: 'Nikola Jokić', team: 'DEN', score: 96.1, trend: 'up', change: 1.2 },
    { id: 2, name: 'Luka Dončić', team: 'DAL', score: 94.2, trend: 'up', change: 1.4 },
    { id: 3, name: 'Jayson Tatum', team: 'BOS', score: 92.8, trend: 'stable', change: 0.3 },
    { id: 4, name: 'Anthony Davis', team: 'LAL', score: 91.5, trend: 'down', change: -1.6 }
  ];
  const myLineup = [
    { name: 'Luka Dončić', pos: 'PG', team: 'DAL', score: 94.2, proj: 55.2 },
    { name: 'Devin Booker', pos: 'SG', team: 'PHX', score: 90.5, proj: 48.5 },
    { name: 'Kevin Durant', pos: 'SF', team: 'PHX', score: 93.8, proj: 52.1 },
    { name: 'Anthony Davis', pos: 'PF', team: 'LAL', score: 91.5, proj: 49.8 },
    { name: 'Nikola Jokić', pos: 'C', team: 'DEN', score: 96.1, proj: 58.3 }
  ];
  const recentAlerts = [
    { id: 1, type: 'positive', player: 'Luka Dončić', message: 'Career-high efficiency week', time: '2h ago' },
    { id: 2, type: 'warning', player: 'Anthony Davis', message: 'Minutes decreased last 3 games', time: '5h ago' },
    { id: 3, type: 'positive', player: 'Jayson Tatum', message: 'Highly consistent performance', time: '1d ago' }
  ];
  const HomeTab = () => (
    <div className="space-y-4 pb-20">
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white">
          <div className="text-sm opacity-90 mb-1">My Lineup Score</div>
          <div className="text-3xl font-bold">93.2</div>
          <div className="text-xs mt-1 flex items-center">
            <TrendingUp className="w-3 h-3 mr-1" />
            <span>+2.4 this week</span>
          </div>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-4 text-white">
          <div className="text-sm opacity-90 mb-1">Projected Points</div>
          <div className="text-3xl font-bold">264</div>
          <div className="text-xs mt-1">Tonight's games</div>
        </div>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="font-semibold text-gray-900">My Lineup</h2>
          <button className="text-blue-600 text-sm font-medium">Edit</button>
        </div>
        <div className="divide-y divide-gray-100">
          {myLineup.map((player, idx) => (
            <div key={idx} className="p-4 flex items-center justify-between active:bg-gray-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-bold text-sm">
                  {player.pos}
                </div>
                <div>
                  <div className="font-medium text-gray-900">{player.name}</div>
                  <div className="text-xs text-gray-500">{player.team}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold text-gray-900">{player.proj}</div>
                <div className="text-xs text-gray-500">pts</div>
              </div>
            </div>
          ))}
        </div>
        <div className="p-4 bg-gray-50 rounded-b-xl">
          <button className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium active:bg-blue-700">
            Optimize Lineup
          </button>
        </div>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Recent Alerts</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {recentAlerts.map(alert => (
            <div key={alert.id} className="p-4 flex items-start gap-3 active:bg-gray-50">
              <div className={`w-2 h-2 rounded-full mt-2 ${
                alert.type === 'positive' ? 'bg-green-500' :
                alert.type === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900 text-sm">{alert.player}</div>
                <div className="text-sm text-gray-600 mt-0.5">{alert.message}</div>
                <div className="text-xs text-gray-400 mt-1">{alert.time}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
  const PlayersTab = () => (
    <div className="space-y-4 pb-20">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Search players..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Top Performers</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {topPlayers.map((player, idx) => (
            <div key={player.id} className="p-4 flex items-center justify-between active:bg-gray-50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-white font-bold text-sm">
                  {idx + 1}
                </div>
                <div>
                  <div className="font-medium text-gray-900">{player.name}</div>
                  <div className="text-xs text-gray-500">{player.team}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold text-lg text-gray-900">{player.score}</div>
                <div className={`text-xs font-medium flex items-center justify-end ${
                  player.trend === 'up' ? 'text-green-600' :
                  player.trend === 'down' ? 'text-red-600' : 'text-gray-500'
                }`}>
                  {player.trend === 'up' ? <TrendingUp className="w-3 h-3 mr-1" /> :
                   player.trend === 'down' ? <TrendingUp className="w-3 h-3 mr-1 rotate-180" /> :
                   <span className="w-3 h-0.5 bg-gray-400 mr-1" />}
                  {player.change > 0 ? '+' : ''}{player.change}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-2">
        {['All', 'PG', 'SG', 'SF', 'PF', 'C'].map(pos => (
          <button
            key={pos}
            className="px-4 py-2 rounded-full bg-gray-100 text-gray-700 text-sm font-medium whitespace-nowrap active:bg-gray-200"
          >
            {pos}
          </button>
        ))}
      </div>
    </div>
  );
  const StatsTab = () => (
    <div className="space-y-4 pb-20">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <h2 className="font-semibold text-gray-900 mb-4">Performance Trends</h2>
        <div className="space-y-3">
          {[
            { label: 'Scoring', value: 92, color: 'bg-blue-500' },
            { label: 'Efficiency', value: 88, color: 'bg-green-500' },
            { label: 'Playmaking', value: 85, color: 'bg-purple-500' },
            { label: 'Defense', value: 78, color: 'bg-red-500' },
            { label: 'Rebounding', value: 82, color: 'bg-yellow-500' }
          ].map(stat => (
            <div key={stat.label}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-700">{stat.label}</span>
                <span className="font-semibold text-gray-900">{stat.value}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`${stat.color} h-2 rounded-full transition-all duration-500`}
                  style={{ width: `${stat.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <h2 className="font-semibold text-gray-900 mb-4">Weekly Performance</h2>
        <div className="grid grid-cols-7 gap-2">
          {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, idx) => (
            <div key={idx} className="text-center">
              <div className="text-xs text-gray-500 mb-2">{day}</div>
              <div className={`h-12 rounded-lg ${
                idx < 4 ? 'bg-green-500' : idx === 4 ? 'bg-yellow-500' : 'bg-gray-200'
              }`} />
              <div className="text-xs font-medium mt-1 text-gray-700">
                {idx < 4 ? '92' : idx === 4 ? '88' : '--'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
  return (
    <div className="min-h-screen bg-gray-50">
      {!isOnline && (
        <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white text-center py-2 text-sm font-medium z-50">
          You are offline. Some features may be limited.
        </div>
      )}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setMenuOpen(true)}
              className="p-2 -ml-2 active:bg-gray-100 rounded-lg"
            >
              <Menu className="w-6 h-6 text-gray-700" />
            </button>
            <div>
              <h1 className="text-lg font-bold text-gray-900">NBA Analytics</h1>
              <p className="text-xs text-gray-500">Fantasy Optimizer</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 relative active:bg-gray-100 rounded-lg">
              <Bell className="w-6 h-6 text-gray-700" />
              {notifications > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-white text-xs flex items-center justify-center">
                  {notifications}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>
      {menuOpen && (
        <>
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={() => setMenuOpen(false)}
          />
          <div className="fixed top-0 left-0 bottom-0 w-80 bg-white z-50 shadow-xl">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-bold text-gray-900">Menu</h2>
              <button 
                onClick={() => setMenuOpen(false)}
                className="p-2 active:bg-gray-100 rounded-lg"
              >
                <X className="w-6 h-6 text-gray-700" />
              </button>
            </div>
            <nav className="p-4 space-y-2">
              {[
                { icon: Home, label: 'Home', id: 'home' },
                { icon: Users, label: 'Players', id: 'players' },
                { icon: BarChart3, label: 'Statistics', id: 'stats' },
                { icon: Activity, label: 'Live Games', id: 'live' },
                { icon: Award, label: 'Leaderboard', id: 'leaderboard' },
                { icon: Settings, label: 'Settings', id: 'settings' }
              ].map(item => (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setMenuOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                    activeTab === item.id
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 active:bg-gray-100'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </>
      )}
      <main className="p-4">
        {activeTab === 'home' && <HomeTab />}
        {activeTab === 'players' && <PlayersTab />}
        {activeTab === 'stats' && <StatsTab />}
      </main>
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40">
        <div className="grid grid-cols-4 gap-1 p-2">
          {[
            { icon: Home, label: 'Home', id: 'home' },
            { icon: Users, label: 'Players', id: 'players' },
            { icon: BarChart3, label: 'Stats', id: 'stats' },
            { icon: Activity, label: 'Live', id: 'live' }
          ].map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg transition ${
                activeTab === item.id
                  ? 'text-blue-600'
                  : 'text-gray-600 active:bg-gray-100'
              }`}
            >
              <item.icon className="w-6 h-6" />
              <span className="text-xs font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
};
export default MobileNBAApp;