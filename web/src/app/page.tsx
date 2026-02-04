"use client";

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Send, Cpu, Globe, Zap, CheckCircle, Copy, ShieldCheck, ChevronDown, Languages, Loader2, Sparkles, Github, Database } from 'lucide-react';
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
      welcome: "Secure Protocol Established. Select a documentation source above to initiate a direct knowledge retrieval session. Accessing official data in real-time.",
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
      welcome: "安全协议已建立。请在上方选择文档源以开启直接检索会话。正在实时接入官方权威知识库。",
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
    fetch('/api/sites')
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
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading || !selectedSite) return;
    
    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    const currentSiteUrl = selectedSite.url;
    setInput("");
    setLoading(true);

    try {
      const response = await fetch('/api/chat', {
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
      setMessages(prev => [...prev, { role: 'assistant', content: "Connection Failed. Check your network." }]);
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

  const scrollingSites1 = ["Langfuse", "Render", "Clerk", "Neon", "React", "Bun", "Zod", "PostHog"];
  const scrollingSites2 = ["Goose", "Zitadel", "Nextra", "LiteLLM", "Frigate", "Fingerprint", "Sui", "Starknet"];

  return (
    <main className="min-h-screen bg-[#030303] text-zinc-100 font-sans selection:bg-emerald-500/30 overflow-x-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[20%] w-[50%] h-[50%] bg-blue-900/10 rounded-full blur-[150px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-900/10 rounded-full blur-[150px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        <header className="flex justify-between items-center mb-20 backdrop-blur-md bg-[#030303]/50 sticky top-0 z-50 py-4 border-b border-zinc-900/50 px-2">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-zinc-900 rounded-lg flex items-center justify-center border border-zinc-800">
              <Cpu size={18} className="text-emerald-500" />
            </div>
            <span className="font-bold text-lg tracking-tight uppercase">inkeep-mcp</span>
          </div>
          
          <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-zinc-500 uppercase tracking-widest">
            <a href="https://github.com/xu-xiang/inkeep-mcp" target="_blank" className="flex items-center gap-2 hover:text-white transition-colors group">
              <Github size={16} className="group-hover:scale-110 transition-transform" />
              <span>{t.nav.github}</span>
            </a>
            <div className="h-4 w-px bg-zinc-800" />
            <button onClick={() => setLang(lang === 'en' ? 'zh' : 'en')} className="flex items-center gap-2 hover:text-white transition-all uppercase">
              <Languages size={14} className="text-emerald-500" /> {lang === 'en' ? '中文' : 'EN'}
            </button>
            <button onClick={copyConfig} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-all flex items-center gap-2 font-bold">
              {copied ? <CheckCircle size={14} /> : <Copy size={14} />}
              <span>{copied ? (lang === 'zh' ? "已复制" : "Copied!") : t.nav.config}</span>
            </button>
          </nav>
        </header>

        <section className="text-center mb-24 pt-10">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-[10px] font-bold uppercase tracking-[0.2em] mb-8">
              <ShieldCheck size={12} /> <span>{t.hero.tag}</span>
            </div>
            <h1 className="text-5xl md:text-8xl font-black tracking-tighter leading-[0.9] mb-8 text-zinc-100 italic uppercase">
              {t.hero.title} <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-blue-400 to-blue-500 uppercase">
                {t.hero.highlight}
              </span>
            </h1>
            <p className="max-w-2xl mx-auto text-zinc-500 text-lg mb-12 leading-relaxed">
              {t.hero.subtitle}
            </p>
            <a href="#demo" className="inline-flex items-center gap-2 px-8 py-4 bg-zinc-100 hover:bg-white text-black font-bold rounded-xl transition-all hover:scale-105">
              <Terminal size={18} /> {t.hero.btnPrimary}
            </a>
          </motion.div>
        </section>

        <div className="mb-48 space-y-4 overflow-hidden relative opacity-30">
          <div className="flex gap-16 whitespace-nowrap animate-infinite-scroll py-2">
            {[...scrollingSites1, ...scrollingSites1].map((s, i) => (
              <div key={i} className="flex items-center gap-3 text-2xl font-black uppercase tracking-tighter">
                <Globe size={18} className="text-blue-500" /> {s}
              </div>
            ))}
          </div>
          <div className="flex gap-16 whitespace-nowrap animate-infinite-scroll-reverse py-2" style={{ animationDuration: '60s' }}>
            {[...scrollingSites2, ...scrollingSites2].map((s, i) => (
              <div key={i} className="flex items-center gap-3 text-2xl font-black uppercase tracking-tighter">
                <Database size={18} className="text-emerald-500" /> {s}
              </div>
            ))}
          </div>
        </div>

        <section id="demo" className="mb-40 scroll-mt-24">
          <div className="relative max-w-5xl mx-auto">
            <div className="absolute -inset-1 bg-gradient-to-b from-emerald-500/20 to-blue-600/20 rounded-[24px] blur-2xl opacity-20" />
            <div className="relative bg-[#080808] border border-zinc-800 rounded-2xl shadow-2xl flex flex-col h-[750px] overflow-hidden">
              <div className="border-b border-zinc-800 bg-[#0c0c0c] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-zinc-800" /><div className="w-2.5 h-2.5 rounded-full bg-zinc-800" /><div className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500 font-bold uppercase tracking-widest flex items-center gap-2">
                     <Terminal size={12} className="text-emerald-500" /> {t.chat.header}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                   <select 
                      className="bg-zinc-900 border border-zinc-700 text-zinc-300 text-xs font-bold py-2 px-4 rounded-lg outline-none cursor-pointer focus:border-emerald-500/50 transition-colors"
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

              <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-8 font-mono text-sm custom-scrollbar bg-[#080808]">
                {messages.map((m, i) => (
                  <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={cn("flex gap-4 max-w-[92%]", m.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto")}>
                    <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center shrink-0 mt-1 shadow-2xl", m.role === 'user' ? "bg-blue-600 border border-blue-400/30" : "bg-zinc-800 border border-zinc-700")}>
                      {m.role === 'user' ? <Sparkles size={18} /> : <Cpu size={18} />}
                    </div>
                    <div className={cn(
                      "p-5 rounded-2xl leading-relaxed text-[15px] shadow-2xl",
                      m.role === 'user' ? "bg-blue-600/10 border border-blue-500/20 text-blue-50" : (m.isStatus ? "text-emerald-400 italic font-medium" : "bg-[#111] border border-zinc-800 text-zinc-200")
                    )}>
                      {m.isStatus && <Loader2 size={14} className="inline mr-2 animate-spin" />}
                      {!m.isStatus ? (
                        <div className="prose prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
                            code({node, inline, className, children, ...props}: any) {
                              const match = /language-(\w+)/.exec(className || '');
                              return !inline && match ? (
                                <div className="rounded-xl overflow-hidden my-6 border border-zinc-700/50 shadow-2xl">
                                  <div className="bg-[#1a1a1a] px-4 py-2 text-[11px] text-zinc-400 border-b border-zinc-800 flex justify-between items-center font-sans">
                                    <span className="uppercase tracking-widest font-bold">{match[1]}</span>
                                    <Copy size={12} className="opacity-50 hover:opacity-100 cursor-pointer" />
                                  </div>
                                  <SyntaxHighlighter style={vscDarkPlus} language={match[1]} PreTag="div" customStyle={{ margin: 0, padding: '1.5rem', background: '#050505', fontSize: '13px', lineHeight: '1.6' }} {...props}>
                                    {String(children).replace(/\n$/, '')}
                                  </SyntaxHighlighter>
                                </div>
                              ) : <code className="bg-zinc-800/80 px-1.5 py-0.5 rounded text-emerald-400 text-[13px] font-bold font-mono" {...props}>{children}</code>;
                            },
                            p: (props) => <p className="mb-4 last:mb-0 leading-relaxed" {...props} />,
                            a: (props) => <a className="text-blue-400 hover:text-blue-300 underline underline-offset-4 font-bold" target="_blank" {...props} />,
                            ul: (props) => <ul className="list-disc list-inside space-y-2 mb-4 text-zinc-300" {...props} />,
                            ol: (props) => <ol className="list-decimal list-inside space-y-2 mb-4 text-zinc-300" {...props} />,
                            li: (props) => <li className="marker:text-emerald-500" {...props} />,
                            h1: (props) => <h1 className="text-xl font-black mt-8 mb-4 text-white border-b border-zinc-800 pb-2" {...props} />,
                            h2: (props) => <h2 className="text-lg font-bold mt-6 mb-3 text-white" {...props} />,
                            table: (props) => <div className="overflow-x-auto my-6 rounded-lg border border-zinc-800"><table className="w-full text-left border-collapse" {...props} /></div>,
                            th: (props) => <th className="bg-zinc-900 p-3 text-xs uppercase tracking-widest font-bold border-b border-zinc-800" {...props} />,
                            td: (props) => <td className="p-3 text-sm border-b border-zinc-800/50" {...props} />,
                          }}>{m.content}</ReactMarkdown>
                          {loading && i === messages.length - 1 && <span className="inline-block w-2 h-4 bg-emerald-500 ml-1 animate-pulse align-middle" />}
                        </div>
                      ) : m.content}
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="p-6 bg-[#0c0c0c] border-t border-zinc-800">
                <div className="relative group max-w-4xl mx-auto">
                   <div className="absolute -inset-0.5 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl blur opacity-0 group-focus-within:opacity-20 transition duration-500" />
                   <div className="relative flex bg-[#050505] border border-zinc-800 rounded-2xl overflow-hidden focus-within:border-emerald-500/50 transition-all">
                    <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSend()} placeholder={t.chat.placeholder}
                      className="flex-1 bg-transparent px-6 py-5 text-[15px] focus:outline-none placeholder:text-zinc-700 text-zinc-100" />
                    <button onClick={handleSend} disabled={loading || !input.trim()} className="px-8 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 transition-colors text-white font-bold">
                      <Send size={20} />
                    </button>
                   </div>
                </div>
                <div className="mt-4 flex justify-between items-center px-4 opacity-50">
                   <span className="text-[10px] font-bold uppercase tracking-[0.3em]">{selectedSite ? `Target: ${new URL(selectedSite.url).hostname}` : "Connecting..."}</span>
                   <span className="text-[10px] font-bold uppercase tracking-[0.3em]">{t.chat.footer}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="mb-40 max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black uppercase tracking-tight mb-4 italic italic">{t.features.title}</h2>
            <p className="text-zinc-500 text-lg mb-8">{t.features.desc}</p>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/5 border border-emerald-500/10 text-emerald-400 text-sm font-bold">
              <Zap size={16} /> {t.features.disclaimer}
            </div>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {t.features.cards.map((card, i) => (
              <div key={i} className="p-10 rounded-3xl bg-[#080808] border border-zinc-800 hover:border-emerald-500/30 transition-all hover:-translate-y-2 group">
                <div className="w-14 h-14 bg-zinc-900 rounded-2xl flex items-center justify-center mb-8 border border-zinc-800 group-hover:scale-110 transition-transform">{card.icon}</div>
                <h3 className="text-xl font-bold mb-4 text-white">{card.title}</h3>
                <p className="text-zinc-500 leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <footer className="border-t border-zinc-900 py-16 text-center opacity-30 hover:opacity-100 transition-opacity">
          <div className="flex justify-center gap-8 mb-8">
             <Github size={20} /><Globe size={20} /><Database size={20} />
          </div>
          <p className="text-[10px] font-black uppercase tracking-[0.4em]">© 2026 INKEEP-MCP · PROTOCOL FOR THE FUTURE</p>
        </footer>
      </div>

      <style jsx global>{`
        @keyframes infinite-scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }
        @keyframes infinite-scroll-reverse { from { transform: translateX(-50%); } to { transform: translateX(0); } }
        .animate-infinite-scroll { animation: infinite-scroll 40s linear infinite; }
        .animate-infinite-scroll-reverse { animation: infinite-scroll-reverse 40s linear infinite; }
        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #222; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #333; }
      `}</style>
    </main>
  );
}
