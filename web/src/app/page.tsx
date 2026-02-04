"use client";

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Send, Cpu, Globe, Zap, CheckCircle, Copy, ShieldCheck, ChevronDown, Languages, Loader2, Sparkles, Github, Database, Cloud, Lock, Server } from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';

// --- Types ---
interface Site {
  id: string;
  name: string;
  url: string;
  description: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  isStatus?: boolean; 
}

// --- Translations ---
const translations = {
  en: {
    nav: { features: "Features", ecosystem: "Ecosystem", demo: "Live Terminal", github: "GitHub", config: "MCP Config" },
    hero: {
      tag: "The Unofficial Universal Connector",
      title: "UNLOCK DOCS AI",
      highlight: "WITHOUT API KEYS",
      subtitle: "Connect your local LLMs directly to Inkeep-powered documentation. Bypass the browser, solve PoW challenges automatically, and query official knowledge bases in real-time.",
      btnPrimary: "Try Live Terminal",
      btnSecondary: "How It Works"
    },
    features: {
      title: "BYPASS THE BROWSER",
      desc: "Inkeep MCP acts as a bridge, simulating legitimate browser traffic to fetch high-quality, verified answers from official documentation sites.",
      disclaimer: "Tested sites above. In principle, any site with Inkeep configuration can be accessed.",
      cards: [
        { title: "Auto-PoW Solver", desc: "Built-in SHA-256 collision algorithm solves Inkeep's Altcha challenges locally in milliseconds.", icon: <ShieldCheck className="text-emerald-400" /> },
        { title: "Zero Configuration", desc: "No API keys needed. Just point to a URL, and the server handles the handshake.", icon: <Zap className="text-yellow-400" /> },
        { title: "Universal Registry", desc: "Support for dozens of top dev tools like Langfuse, Render, Neon, and PostHog.", icon: <Globe className="text-blue-400" /> }
      ]
    },
    chat: {
      header: "inkeep-mcp-interactive",
      status: "System Online",
      select: "Select Knowledge Base:",
      placeholder: "Ask a technical question...",
      welcome: "Welcome. Select a documentation source above and ask any question. Note: Any Inkeep-supported site works beyond this list.",
      footer: "Powered by inkeep-mcp core | v1.0.4"
    }
  },
  zh: {
    nav: { features: "核心特性", ecosystem: "支持列表", demo: "实时终端", github: "GitHub", config: "MCP 配置" },
    hero: {
      tag: "非官方通用连接器",
      title: "解锁文档 AI",
      highlight: "无需 API KEY",
      subtitle: "将您的本地 LLM 直接连接到 Inkeep 驱动的文档库。绕过浏览器限制，自动通过 PoW 验证，实时查询官方技术知识库。",
      btnPrimary: "进入实时终端",
      btnSecondary: "工作原理"
    },
    features: {
      title: "突破浏览器限制",
      desc: "Inkeep MCP 充当智能桥梁，模拟合法的浏览器流量，从官方文档站点获取经过验证的高质量解答。",
      disclaimer: "以上为已测试站点。原则上，任何集成了 Inkeep 的网站都可以通过本项目访问。",
      cards: [
        { title: "自动 PoW 过盾", desc: "内置 SHA-256 碰撞算法，毫秒级在本地破解 Inkeep 的 Altcha 人机验证。", icon: <ShieldCheck className="text-emerald-400" /> },
        { title: "零配置启动", desc: "不需要申请任何 API Key。只需指定 URL，服务器自动完成握手和鉴权。", icon: <Zap className="text-yellow-400" /> },
        { title: "通用注册表", desc: "预置了 Langfuse, Render, Neon, PostHog 等数十个顶级开发工具。", icon: <Globe className="text-blue-400" /> }
      ]
    },
    chat: {
      header: "inkeep-mcp-交互终端",
      status: "系统在线",
      select: "选择知识库:",
      placeholder: "输入技术问题...",
      welcome: "欢迎。请选择一个文档源并提问。提示：本列表外任何支持 Inkeep 的站点原则上均可访问。",
      footer: "由 inkeep-mcp 核心驱动 | v1.0.4"
    }
  }
};

export default function Home() {
  const [lang, setLang] = useState<'en' | 'zh'>('zh');
  const t = translations[lang];
  
  const [sites, setSites] = useState<Site[]>([]);
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('http://localhost:3002/api/sites')
      .then(res => res.json())
      .then(data => {
        setSites(data);
        if (data.length > 0) setSelectedSite(data[0]);
      })
      .catch(err => console.error("Failed to load sites", err));
  }, []);

  useEffect(() => {
    setMessages([{ role: 'assistant', content: t.chat.welcome }]);
  }, [lang, t.chat.welcome]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading || !selectedSite) return;
    
    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    const currentSiteUrl = selectedSite.url;
    setInput("");
    setLoading(true);

    try {
      const response = await fetch('http://localhost:3002/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: currentInput, url: currentSiteUrl }),
      });

      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let assistantMsg: Message = { role: 'assistant', content: "" };
      setMessages(prev => [...prev, assistantMsg]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(Boolean);
        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            if (data.type === 'status') {
               setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1] = { role: 'assistant', content: `[SYSTEM] ${data.content}`, isStatus: true };
                  return newMsgs;
               });
            } else if (data.type === 'delta') {
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsg = newMsgs[newMsgs.length - 1];
                const prevContent = lastMsg.isStatus ? "" : lastMsg.content;
                newMsgs[newMsgs.length - 1] = { role: 'assistant', content: prevContent + data.content, isStatus: false };
                return newMsgs;
              });
            } else if (data.type === 'error') {
               setMessages(prev => [...prev, { role: 'assistant', content: `\n[ERROR] ${data.content}` }]);
            }
          } catch (e) { }
        }
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Connection Failed. Is the backend running?" }]);
    } finally {
      setLoading(false);
    }
  };

  const copyConfig = () => {
    const config = `{ "mcpServers": { "inkeep": { "command": "python3", "args": ["${process.cwd()}/mcp_server.py"] } } }`;
    navigator.clipboard.writeText(config);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Full list of supported sites for the visual scroll
  const scrollingSites1 = [
    "Langfuse", "Render", "Clerk", "Neon", "Teleport", "React", "Bootstrap", "Ragflow", "Node", "Socket-io", "Sway"
  ];
  const scrollingSites2 = [
    "Bun", "Zod", "Novu", "LiteLLM", "PostHog", "Goose", "Frigate", "FingerprintJS", "SpacetimeDB", "Nextra", "Zitadel"
  ];

  return (
    <main className="min-h-screen bg-[#050505] text-zinc-100 font-sans selection:bg-emerald-500/30 overflow-x-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[20%] w-[50%] h-[50%] bg-blue-900/10 rounded-full blur-[150px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-900/10 rounded-full blur-[150px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        {/* Navbar */}
        <header className="flex justify-between items-center mb-20 backdrop-blur-md bg-[#050505]/50 sticky top-0 z-50 py-4 border-b border-zinc-900/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-zinc-900 rounded-lg flex items-center justify-center border border-zinc-800 shadow-xl shadow-emerald-500/5">
              <Cpu size={18} className="text-emerald-500" />
            </div>
            <span className="font-bold text-lg tracking-tight uppercase">inkeep-mcp</span>
          </div>
          
          <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-zinc-500 uppercase tracking-widest">
            {Object.entries(t.nav).map(([key, value]) => (
              key !== 'config' && key !== 'github' && <a key={key} href={`#${key}`} className="hover:text-emerald-400 transition-colors">{value}</a>
            ))}
            
            <a href="https://github.com/xu-xiang/inkeep-mcp" target="_blank" className="flex items-center gap-2 hover:text-white transition-colors group">
              <Github size={16} className="group-hover:scale-110 transition-transform" />
              <span>{t.nav.github}</span>
            </a>

            <div className="h-4 w-px bg-zinc-800 mx-2" />
            
            <button onClick={() => setLang(lang === 'en' ? 'zh' : 'en')} className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-zinc-900 transition-colors">
              <Languages size={14} /> {lang === 'en' ? '中文' : 'EN'}
            </button>

            <button onClick={copyConfig} className="px-4 py-2 bg-zinc-100 hover:bg-white text-black rounded-lg transition-all flex items-center gap-2 font-bold">
              {copied ? <CheckCircle size={14} className="text-emerald-600" /> : <Copy size={14} />}
              <span>{copied ? (lang === 'zh' ? "已复制" : "Copied!") : t.nav.config}</span>
            </button>
          </nav>
        </header>

        {/* Hero */}
        <section className="text-center mb-24 pt-10">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-[10px] font-bold uppercase tracking-[0.2em] mb-8">
              <ShieldCheck size={12} />
              <span>{t.hero.tag}</span>
            </div>
            
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-[0.9] mb-8 text-zinc-100 italic">
              {t.hero.title} <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-blue-400 to-blue-500">
                {t.hero.highlight}
              </span>
            </h1>
            
            <p className="max-w-2xl mx-auto text-zinc-500 text-lg mb-12 leading-relaxed">
              {t.hero.subtitle}
            </p>

            <div className="flex justify-center gap-4">
              <a href="#demo" className="px-8 py-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-2">
                <Terminal size={18} /> {t.hero.btnPrimary}
              </a>
            </div>
          </motion.div>
        </section>

        {/* Dynamic Ecosystem Wall (Double Scrolling) */}
        <motion.div 
          initial={{ opacity: 0, y: 50 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ delay: 0.5, duration: 1 }}
          className="mb-48 space-y-4 overflow-hidden relative"
        >
          <div className="absolute inset-y-0 left-0 w-40 bg-gradient-to-r from-[#050505] to-transparent z-10" />
          <div className="absolute inset-y-0 right-0 w-40 bg-gradient-to-l from-[#050505] to-transparent z-10" />
          
          {/* Row 1: Left */}
          <div className="flex gap-16 whitespace-nowrap animate-infinite-scroll py-2 opacity-40 hover:opacity-100 transition-opacity duration-500">
            {[...scrollingSites1, ...scrollingSites1, ...scrollingSites1].map((site, i) => (
              <div key={i} className="flex items-center gap-3 grayscale hover:grayscale-0 transition-all cursor-default">
                <Globe size={18} className="text-blue-500" />
                <span className="text-2xl font-black tracking-tighter uppercase">{site}</span>
              </div>
            ))}
          </div>

          {/* Row 2: Right (Reverse) */}
           <div className="flex gap-16 whitespace-nowrap animate-infinite-scroll-reverse py-2 opacity-40 hover:opacity-100 transition-opacity duration-500" style={{ animationDuration: '50s' }}>
            {[...scrollingSites2, ...scrollingSites2, ...scrollingSites2].map((site, i) => (
              <div key={i} className="flex items-center gap-3 grayscale hover:grayscale-0 transition-all cursor-default">
                <Database size={18} className="text-emerald-500" />
                <span className="text-2xl font-black tracking-tighter uppercase">{site}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Demo */}
        <section id="demo" className="mb-40 scroll-mt-24">
          <div className="relative max-w-5xl mx-auto">
            <div className="absolute -inset-1 bg-gradient-to-b from-emerald-500/10 to-blue-600/10 rounded-[24px] blur-2xl opacity-30" />
            <div className="relative bg-[#0A0A0A] border border-zinc-800 rounded-2xl shadow-2xl flex flex-col h-[700px] overflow-hidden">
              <div className="border-b border-zinc-800 bg-zinc-900/30 p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="flex gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-zinc-800" /><div className="w-2.5 h-2.5 rounded-full bg-zinc-800" /><div className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500 font-bold uppercase tracking-widest flex items-center gap-2">
                     <Terminal size={12} className="text-blue-500" /> {t.chat.header}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                   <select 
                      className="bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs font-bold py-2 px-4 rounded-lg outline-none min-w-[180px]"
                      onChange={(e) => {
                        const site = sites.find(s => s.url === e.target.value);
                        if(site) setSelectedSite(site);
                      }}
                      value={selectedSite?.url || ""}
                   >
                     {sites.map(s => <option key={s.id} value={s.url}>{s.name}</option>)}
                   </select>
                   <div className="flex items-center gap-2 text-[10px] text-emerald-500 font-bold uppercase tracking-wider bg-emerald-500/10 px-2 py-1 rounded">
                     <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> {t.chat.status}
                   </div>
                </div>
              </div>

              <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 font-mono text-sm custom-scrollbar">
                {messages.map((m, i) => (
                  <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className={cn("flex gap-4 max-w-[90%]", m.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto")}>
                    <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-1 shadow-inner", m.role === 'user' ? "bg-blue-600" : "bg-zinc-800")}>
                      {m.role === 'user' ? <Sparkles size={16} /> : <Cpu size={16} />}
                    </div>
                    <div className={cn("p-4 rounded-xl leading-relaxed text-sm overflow-hidden", m.role === 'user' ? "bg-blue-600/5 border border-blue-500/20 text-blue-100" : (m.isStatus ? "text-emerald-400 italic" : "bg-zinc-900 border border-zinc-800 text-zinc-300 shadow-xl"))}>
                      {!m.isStatus ? (
                        <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
                          code({node, inline, className, children, ...props}: any) {
                            const match = /language-(\w+)/.exec(className || '');
                            return !inline && match ? (
                              <div className="rounded-lg overflow-hidden my-3 border border-zinc-700 shadow-2xl">
                                <div className="bg-zinc-800 px-3 py-1 text-[9px] text-zinc-500 border-b border-zinc-700">{match[1]}</div>
                                <SyntaxHighlighter style={vscDarkPlus} language={match[1]} PreTag="div" customStyle={{ margin: 0, background: '#0D0D0D', fontSize: '0.85em' }} {...props}>{String(children).replace(/\n$/, '')}</SyntaxHighlighter>
                              </div>
                            ) : <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-emerald-300 text-[11px] font-mono" {...props}>{children}</code>;
                          },
                          a: (props) => <a className="text-blue-400 underline" target="_blank" {...props} />,
                          p: (props) => <p className="mb-2 last:mb-0" {...props} />,
                        }}>{m.content}</ReactMarkdown>
                      ) : (<span><Loader2 size={12} className="inline mr-2 animate-spin" />{m.content}</span>)}
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="p-4 bg-zinc-900/20 border-t border-zinc-800">
                <div className="relative group">
                  <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSend()} placeholder={t.chat.placeholder}
                    className="w-full bg-zinc-950 border border-zinc-800 focus:border-emerald-500/50 rounded-xl py-4 pl-5 pr-14 text-sm focus:outline-none transition-all" />
                  <button onClick={handleSend} disabled={loading || !input.trim()} className="absolute right-2 top-2 p-2 bg-zinc-800 hover:bg-emerald-600 text-zinc-400 hover:text-white rounded-lg transition-colors"><Send size={18} /></button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features & Disclaimer */}
        <section id="features" className="mb-40">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-black uppercase tracking-tight mb-4 italic">{t.features.title}</h2>
            <p className="text-zinc-500 max-w-2xl mx-auto mb-4">{t.features.desc}</p>
            <div className="inline-block p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10 text-emerald-400/80 text-xs font-bold">
              <Zap size={14} className="inline mr-2" /> {t.features.disclaimer}
            </div>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {t.features.cards.map((card, i) => (
              <div key={i} className="p-8 rounded-2xl bg-zinc-900/10 border border-zinc-800 hover:border-emerald-500/20 transition-all hover:-translate-y-1 group">
                <div className="w-12 h-12 bg-zinc-900 rounded-xl flex items-center justify-center mb-6 border border-zinc-800 group-hover:scale-110 transition-transform">{card.icon}</div>
                <h3 className="text-lg font-bold mb-3 text-zinc-200">{card.title}</h3>
                <p className="text-sm text-zinc-500 leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <footer className="border-t border-zinc-900 py-12 text-center opacity-40 hover:opacity-100 transition-opacity">
          <p className="text-zinc-600 text-[10px] font-bold uppercase tracking-[0.3em]">© 2026 Inkeep-MCP · Built for Knowledge Access</p>
        </footer>
      </div>

      <style jsx global>{`
        @keyframes infinite-scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }
        @keyframes infinite-scroll-reverse { from { transform: translateX(-50%); } to { transform: translateX(0); } }
        .animate-infinite-scroll { animation: infinite-scroll 40s linear infinite; }
        .animate-infinite-scroll-reverse { animation: infinite-scroll-reverse 40s linear infinite; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #222; border-radius: 10px; }
      `}</style>
    </main>
  );
}