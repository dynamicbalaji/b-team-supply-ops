import AgentNetwork from './AgentNetwork';
import Chat from './Chat';

const SidePanel = () => {
  return (
    <div className="flex flex-col bg-[#0a1218] min-h-0 shadow-xl shadow-black/20 h-full overflow-hidden">
      <AgentNetwork />
      <Chat />
    </div>
  );
};

export default SidePanel;
