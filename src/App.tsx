import { useState, useEffect, useRef, ChangeEvent } from "react";
import { 
  GitBranch, 
  Folder, 
  Github, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Trash2, 
  FileText, 
  Terminal,
  ChevronRight,
  History,
  ShieldCheck,
  Zap,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Bot,
  User as UserIcon,
  MessageSquare
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { api, AuditLog, SyncStatus } from "./services/api";
import { summarizeDiff, generateSpeech } from "./services/gemini";

type Step = "setup" | "verify" | "sync" | "cleanup" | "done";

interface Message {
  role: "agent" | "user";
  text: string;
  timestamp: Date;
}

export default function App() {
  const [step, setStep] = useState<Step>("setup");
  const [localPath, setLocalPath] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("dev");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [deleteConfirmed, setDeleteConfirmed] = useState(false);
  
  // Browser State
  const [showBrowser, setShowBrowser] = useState(false);
  const [browserData, setBrowserData] = useState<{ currentPath: string; parentPath: string; directories: { name: string; path: string }[] } | null>(null);
  
  // Voice & Chat State
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      text: "GitSync Agent initialized. Please configure the target repository and local path to begin.",
      timestamp: new Date()
    }
  ]);
  
  const logEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isInitialMount = useRef(true);

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    if (messages.length > 1) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleBrowse = async (path?: string) => {
    setLoading(true);
    try {
      const data = await api.ls(path);
      setBrowserData(data);
      setShowBrowser(true);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const selectDirectory = (path: string) => {
    setLocalPath(path);
    setShowBrowser(false);
    addMessage("agent", `Target path set to: ${path}`);
  };

  const addMessage = (role: "agent" | "user", text: string) => {
    setMessages(prev => [...prev, { role, text, timestamp: new Date() }]);
    if (role === "agent" && isVoiceEnabled) {
      speak(text);
    }
  };

  const speak = async (text: string) => {
    const audioUrl = await generateSpeech(text);
    if (audioUrl) {
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
      }
    }
  };

  const fetchLogs = async () => {
    try {
      const data = await api.getLogs();
      setLogs(data);
    } catch (err) {
      console.error("Failed to fetch logs", err);
    }
  };

  const handleInit = async () => {
    setLoading(true);
    setError(null);
    addMessage("agent", "Initializing Input Agent. Validating repository path and remote connectivity...");
    try {
      await api.init(localPath, repoUrl, branch);
      addMessage("agent", "Initialization successful. Passing control to Sync Agent.");
      setStep("verify");
      handleVerify();
    } catch (err: any) {
      const msg = err.message.includes("Path does not exist") 
        ? `Validation Error: The path "${localPath}" was not found on the server. Please use the 'Browse' button to select a directory within the agent's environment (e.g., /app/applet).`
        : err.message;
      setError(msg);
      addMessage("agent", `Initialization failed: ${msg}`);
    } finally {
      setLoading(false);
      fetchLogs();
    }
  };

  const handleVerify = async () => {
    setLoading(true);
    setError(null);
    addMessage("agent", "Sync Agent active. Fetching remote status and calculating differences...");
    try {
      const status = await api.verify(localPath, branch);
      setSyncStatus(status);
      
      addMessage("agent", "Analysis Agent engaged. Interpreting raw git data...");
      const summary = await summarizeDiff(status.diff);
      setAiSummary(summary);
      addMessage("agent", summary);

      if (status.isSynced) {
        addMessage("agent", "Local and remote are in sync. We can proceed to README update.");
      } else {
        addMessage("agent", "Differences detected. Please review the summary before proceeding.");
      }
    } catch (err: any) {
      setError(err.message);
      addMessage("agent", `Verification failed: ${err.message}`);
    } finally {
      setLoading(false);
      fetchLogs();
    }
  };

  const handleSync = async () => {
    setLoading(true);
    setError(null);
    addMessage("agent", "Update Agent active. Modifying README and pushing to remote...");
    try {
      await api.updateReadme(localPath, branch, aiSummary || "");
      addMessage("agent", "README updated and pushed successfully. Verification confirmed.");
      setStep("cleanup");
      addMessage("agent", "Confirmation Agent active. I need your explicit approval to delete the local folder. Do you confirm deletion?");
    } catch (err: any) {
      setError(err.message);
      addMessage("agent", `Sync failed: ${err.message}`);
    } finally {
      setLoading(false);
      fetchLogs();
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirmed) return;
    setLoading(true);
    setError(null);
    addMessage("agent", "Cleanup Agent active. Executing permanent deletion of local folder...");
    try {
      await api.deleteFolder(localPath, true);
      addMessage("agent", "Cleanup complete. All agents have finished their tasks. Audit trail finalized.");
      setStep("done");
    } catch (err: any) {
      setError(err.message);
      addMessage("agent", `Deletion failed: ${err.message}`);
    } finally {
      setLoading(false);
      fetchLogs();
    }
  };

  const startListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      addMessage("agent", "Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript.toLowerCase();
      addMessage("user", transcript);
      
      if (step === "cleanup") {
        if (transcript.includes("yes") || transcript.includes("confirm") || transcript.includes("delete")) {
          setDeleteConfirmed(true);
          addMessage("agent", "Confirmation received. Proceeding with deletion.");
        } else if (transcript.includes("no") || transcript.includes("cancel") || transcript.includes("stop")) {
          addMessage("agent", "Deletion cancelled by user.");
        }
      }
    };
    recognition.start();
  };

  const reset = () => {
    setStep("setup");
    setLocalPath("");
    setRepoUrl("");
    setBranch("dev");
    setSyncStatus(null);
    setAiSummary(null);
    setDeleteConfirmed(false);
    setError(null);
    setMessages([]);
    addMessage("agent", "System reset. Ready for new instructions.");
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-[#E4E3E0] font-sans selection:bg-[#F27D26] selection:text-black">
      <audio ref={audioRef} hidden />
      
      {/* Background Grid */}
      <div className="fixed inset-0 pointer-events-none opacity-10" 
           style={{ backgroundImage: "linear-gradient(#141414 1px, transparent 1px), linear-gradient(90deg, #141414 1px, transparent 1px)", backgroundSize: "40px 40px" }} />

      <header className="border-b border-[#141414] p-6 flex justify-between items-center bg-[#0A0A0A]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-[#F27D26] rounded-lg flex items-center justify-center text-black">
            <Zap size={24} strokeWidth={2.5} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight uppercase italic font-serif">GitSync Agent</h1>
            <p className="text-[10px] uppercase tracking-widest opacity-50 font-mono">Agentic Repository Lifecycle</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setIsVoiceEnabled(!isVoiceEnabled)}
            className={`p-2 rounded-full transition-colors ${isVoiceEnabled ? 'bg-[#F27D26] text-black' : 'bg-[#141414] text-white/50 hover:text-white'}`}
            title={isVoiceEnabled ? "Disable Voice" : "Enable Voice"}
          >
            {isVoiceEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
          </button>
          <div className="flex items-center gap-2 px-3 py-1 bg-[#141414] rounded-full border border-[#222]">
            <div className={`w-2 h-2 rounded-full ${loading ? 'bg-yellow-500 animate-pulse' : 'bg-emerald-500'}`} />
            <span className="text-[10px] font-mono uppercase tracking-wider">{loading ? 'Processing' : 'System Ready'}</span>
          </div>
          <button onClick={reset} className="text-[10px] uppercase tracking-widest opacity-50 hover:opacity-100 transition-opacity">Reset Session</button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Control & Chat */}
        <div className="lg:col-span-8 space-y-8 flex flex-col min-h-[calc(100vh-160px)]">
          
          {/* Contextual Controls - MOVED TO TOP */}
          <div className="h-auto space-y-4">
            <div className="flex items-center gap-2 px-2">
              <Terminal size={14} className="opacity-50" />
              <h3 className="text-[10px] uppercase tracking-widest font-bold opacity-50">Agent Configuration & Controls</h3>
            </div>
            <AnimatePresence mode="wait">
              {step === "setup" && (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="bg-[#141414] border border-[#222] rounded-2xl p-6 space-y-6"
                >
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                    <div className="md:col-span-5 space-y-2">
                      <label className="text-[10px] uppercase tracking-widest opacity-50 font-mono flex items-center gap-2">
                        <Folder size={12} /> Local Path
                      </label>
                      <div className="flex gap-2">
                        <input 
                          type="text" 
                          value={localPath}
                          onChange={(e) => setLocalPath(e.target.value)}
                          placeholder="/path/to/project"
                          className="flex-1 bg-black border border-[#333] rounded-xl px-4 py-2 focus:outline-none focus:border-[#F27D26] transition-colors font-mono text-xs"
                        />
                        <button 
                          onClick={() => handleBrowse()}
                          className="px-3 py-2 bg-[#141414] border border-[#333] rounded-xl hover:bg-[#222] transition-colors text-[10px] uppercase tracking-widest font-bold flex items-center gap-2 shrink-0"
                        >
                          <Folder size={14} className="text-[#F27D26]" /> 
                          <span className="hidden sm:inline">Browse</span>
                        </button>
                      </div>
                    </div>
                    <div className="md:col-span-4 space-y-2">
                      <label className="text-[10px] uppercase tracking-widest opacity-50 font-mono flex items-center gap-2">
                        <Github size={12} /> Repo URL
                      </label>
                      <input 
                        type="text" 
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        placeholder="https://github.com/..."
                        className="w-full bg-black border border-[#333] rounded-xl px-4 py-2 focus:outline-none focus:border-[#F27D26] transition-colors font-mono text-xs"
                      />
                    </div>
                    <div className="md:col-span-3 space-y-2">
                      <label className="text-[10px] uppercase tracking-widest opacity-50 font-mono flex items-center gap-2">
                        <GitBranch size={12} /> Branch
                      </label>
                      <input 
                        type="text" 
                        value={branch}
                        onChange={(e) => setBranch(e.target.value)}
                        placeholder="dev"
                        className="w-full bg-black border border-[#333] rounded-xl px-4 py-2 focus:outline-none focus:border-[#F27D26] transition-colors font-mono text-xs"
                      />
                    </div>
                  </div>
                  <button 
                    onClick={handleInit}
                    disabled={loading || !localPath || !repoUrl}
                    className="w-full bg-[#F27D26] hover:bg-[#ff8c3a] disabled:opacity-50 text-black font-bold py-3 rounded-xl transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-[10px]"
                  >
                    {loading ? <RefreshCw className="animate-spin" size={14} /> : <ShieldCheck size={14} />}
                    Initialize Agents
                  </button>
                </motion.div>
              )}

              {step === "verify" && (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-4"
                >
                  <button 
                    onClick={handleVerify}
                    className="flex-1 bg-[#141414] hover:bg-[#1a1a1a] border border-[#333] text-white font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-xs"
                  >
                    <RefreshCw size={16} /> Re-Verify
                  </button>
                  <button 
                    onClick={handleSync}
                    disabled={loading || !syncStatus?.isSynced && syncStatus?.ahead === 0 && syncStatus?.behind === 0 && !syncStatus?.hasDiff}
                    className="flex-1 bg-[#F27D26] hover:bg-[#ff8c3a] text-black font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-xs"
                  >
                    <FileText size={16} /> Update & Sync
                  </button>
                </motion.div>
              )}

              {step === "cleanup" && (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 text-red-400">
                      <Trash2 size={20} />
                      <span className="text-xs font-bold uppercase tracking-widest">Final Confirmation Required</span>
                    </div>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={deleteConfirmed}
                        onChange={(e) => setDeleteConfirmed(e.target.checked)}
                        className="w-4 h-4 rounded border-[#333] bg-black text-red-500 focus:ring-red-500"
                      />
                      <span className="text-[10px] uppercase tracking-widest opacity-60">Manual Override</span>
                    </label>
                  </div>
                  <button 
                    onClick={handleDelete}
                    disabled={!deleteConfirmed || loading}
                    className="w-full bg-red-500 hover:bg-red-600 disabled:opacity-30 text-white font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-xs"
                  >
                    {loading ? <RefreshCw className="animate-spin" size={18} /> : <Trash2 size={18} />}
                    Execute Permanent Deletion
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Agent Chat Interface */}
          <div className="flex-1 max-h-[500px] bg-[#141414] border border-[#222] rounded-2xl overflow-hidden flex flex-col shadow-2xl">
            <div className="p-4 border-b border-[#222] bg-black/30 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Bot size={16} className="text-[#F27D26]" />
                <span className="text-[10px] uppercase tracking-widest font-bold opacity-70">Agent Communication Hub</span>
              </div>
              {step === "cleanup" && (
                <button 
                  onClick={startListening}
                  className={`flex items-center gap-2 px-3 py-1 rounded-full text-[10px] uppercase tracking-widest transition-all ${isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-[#F27D26] text-black hover:bg-[#ff8c3a]'}`}
                >
                  {isListening ? <Mic size={12} /> : <Mic size={12} />}
                  {isListening ? 'Listening...' : 'Voice Input'}
                </button>
              )}
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
              <AnimatePresence initial={false}>
                {messages.map((msg, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, x: msg.role === 'agent' ? -20 : 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${msg.role === 'agent' ? 'bg-[#F27D26] text-black' : 'bg-[#333] text-white'}`}>
                      {msg.role === 'agent' ? <Bot size={16} /> : <UserIcon size={16} />}
                    </div>
                    <div className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${msg.role === 'agent' ? 'bg-black/50 border border-[#222] rounded-tl-none' : 'bg-[#F27D26] text-black font-medium rounded-tr-none'}`}>
                      {msg.text}
                      <p className={`text-[8px] mt-2 opacity-40 font-mono ${msg.role === 'user' ? 'text-black/60' : ''}`}>
                        {msg.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={chatEndRef} />
            </div>
          </div>
        </div>

        {/* Right Column: Stats & Audit */}
        <div className="lg:col-span-4 space-y-6 h-[calc(100vh-160px)] flex flex-col">
          
          {/* Sync Status Card */}
          <div className="bg-[#141414] border border-[#222] rounded-2xl p-6 space-y-4 shadow-xl">
            <h3 className="text-[10px] uppercase tracking-[0.2em] font-bold opacity-50 flex items-center gap-2">
              <RefreshCw size={12} /> Sync Status
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/30 p-4 rounded-xl border border-[#222] text-center">
                <p className="text-[8px] uppercase opacity-40 mb-1">Behind</p>
                <p className={`text-2xl font-serif italic ${syncStatus?.behind ? 'text-red-400' : 'opacity-20'}`}>{syncStatus?.behind ?? 0}</p>
              </div>
              <div className="bg-black/30 p-4 rounded-xl border border-[#222] text-center">
                <p className="text-[8px] uppercase opacity-40 mb-1">Ahead</p>
                <p className={`text-2xl font-serif italic ${syncStatus?.ahead ? 'text-emerald-400' : 'opacity-20'}`}>{syncStatus?.ahead ?? 0}</p>
              </div>
            </div>
            {syncStatus && (
              <div className={`p-3 rounded-xl border flex items-center justify-center gap-2 text-[10px] font-bold uppercase tracking-widest ${syncStatus.isSynced ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500' : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-500'}`}>
                {syncStatus.isSynced ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                {syncStatus.isSynced ? 'Fully Synchronized' : 'Divergence Detected'}
              </div>
            )}
          </div>

          {/* Audit Trail */}
          <div className="flex-1 bg-[#141414] border border-[#222] rounded-2xl overflow-hidden flex flex-col shadow-xl">
            <div className="p-4 border-b border-[#222] bg-black/30 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <History size={14} className="opacity-50" />
                <span className="text-[10px] uppercase tracking-widest font-bold opacity-50">Audit Trail</span>
              </div>
              <span className="text-[8px] font-mono opacity-30">{logs.length} entries</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide">
              {logs.map((log, i) => (
                <div key={i} className="space-y-1 border-l border-[#333] pl-4 relative">
                  <div className={`absolute left-[-4.5px] top-1.5 w-2 h-2 rounded-full ${log.result === 'Success' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <div className="flex justify-between items-start">
                    <p className="text-[8px] font-mono opacity-40">{new Date(log.timestamp).toLocaleTimeString()}</p>
                  </div>
                  <p className="text-[10px] font-bold tracking-tight">{log.action}</p>
                  {log.details && (
                    <pre className="text-[8px] font-mono opacity-30 bg-black/30 p-2 rounded overflow-x-auto max-h-20">
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>
        </div>
      </main>

      {/* File Browser Modal */}
      <AnimatePresence>
        {showBrowser && browserData && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#141414] border border-[#222] w-full max-w-2xl rounded-2xl overflow-hidden flex flex-col shadow-2xl max-h-[80vh]"
            >
              <div className="p-4 border-b border-[#222] bg-black/30 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <Folder size={16} className="text-[#F27D26]" />
                  <span className="text-[10px] uppercase tracking-widest font-bold opacity-70">Server Directory Browser</span>
                </div>
                <button 
                  onClick={() => setShowBrowser(false)}
                  className="text-[10px] uppercase tracking-widest opacity-50 hover:opacity-100"
                >
                  Close
                </button>
              </div>
              
              <div className="p-4 bg-black/20 border-b border-[#222] flex items-center gap-2 overflow-x-auto scrollbar-hide">
                <button 
                  onClick={() => handleBrowse(browserData.parentPath)}
                  className="p-1 hover:bg-[#222] rounded transition-colors"
                >
                  <ChevronRight size={14} className="rotate-180" />
                </button>
                <span className="text-[10px] font-mono opacity-50 whitespace-nowrap">{browserData.currentPath}</span>
              </div>

              <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-hide">
                {browserData.directories.length === 0 && (
                  <div className="p-8 text-center opacity-30 text-xs uppercase tracking-widest">No subdirectories found</div>
                )}
                {browserData.directories.map((dir, i) => (
                  <div 
                    key={i}
                    className="group flex items-center justify-between p-3 hover:bg-[#222] rounded-xl transition-colors cursor-pointer"
                    onClick={() => handleBrowse(dir.path)}
                  >
                    <div className="flex items-center gap-3">
                      <Folder size={16} className="text-[#F27D26] opacity-50 group-hover:opacity-100" />
                      <span className="text-xs font-mono">{dir.name}</span>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        selectDirectory(dir.path);
                      }}
                      className="opacity-0 group-hover:opacity-100 px-3 py-1 bg-[#F27D26] text-black text-[10px] uppercase tracking-widest font-bold rounded-lg transition-all"
                    >
                      Select
                    </button>
                  </div>
                ))}
              </div>
              
              <div className="p-4 border-t border-[#222] bg-black/30 flex justify-end">
                <button 
                  onClick={() => selectDirectory(browserData.currentPath)}
                  className="px-6 py-2 bg-[#F27D26] text-black text-[10px] uppercase tracking-widest font-bold rounded-xl hover:bg-[#ff8c3a] transition-all"
                >
                  Select Current Directory
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
