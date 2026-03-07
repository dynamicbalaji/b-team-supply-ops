import { useAppStore } from '../../store/useAppStore';
import MapTab from '../Tabs/MapTab/MapTab';
import SplitTab from '../Tabs/SplitTab/SplitTab';
import DecisionTab from '../Tabs/DecisionTab/DecisionTab';
import AuditTab from '../Tabs/AuditTab/AuditTab';
import SidePanel from '../SidePanel/SidePanel';

const MainContent = () => {
  const { activeTab, setActiveTab } = useAppStore();

  const tabs = [
    { id: 'map', label: '🗺 Live Map', component: MapTab },
    { id: 'split', label: '⚡ Traditional vs AI', component: SplitTab },
    { id: 'decision', label: '📊 Decision Matrix', component: DecisionTab },
    { id: 'audit', label: '📋 Audit Trail', component: AuditTab }
  ];

  const ActiveTabComponent = tabs.find(tab => tab.id === activeTab)?.component || MapTab;

  return (
    <div className="grid grid-cols-[1fr_358px] flex-1 min-h-0 overflow-hidden">
      {/* Left Side - Tabs */}
      <div className="flex flex-col border-r border-[#1d2d40] overflow-hidden">
        {/* Tab Header */}
        <div className="flex bg-[#090e15] border-b border-[#1d2d40] px-3 flex-shrink-0">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-[14px] py-[10px] text-[11px] font-bold cursor-pointer border-b-2 border-transparent whitespace-nowrap transition-all duration-200 ${
                activeTab === tab.id
                  ? 'text-[#00d4ff] border-[#00d4ff]'
                  : 'text-[#3d5a72] hover:text-[#9abccc]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden flex flex-col min-h-0">
          <ActiveTabComponent />
        </div>
      </div>

      {/* Right Side - Agents & Chat */}
      <SidePanel />
    </div>
  );
};

export default MainContent;
