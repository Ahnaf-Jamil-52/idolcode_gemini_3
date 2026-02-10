import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Editor from '@monaco-editor/react';
import LatexRenderer from '../components/LatexRenderer';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';
import {
  ChevronLeft,
  ChevronRight,
  FlaskConical,
  Moon,
  Timer,
  Plus,
  Upload,
  Send,
  ExternalLink,
  Loader2,
  X,
  Clock,
  FileCode,
  MessageCircle,
  ArrowLeft,
  Lock,
  Sparkles,
  Swords,
  ChevronDown,
  Pause,
  Play
} from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { ScrollArea } from '../components/ui/scroll-area';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

// Language configurations
const LANGUAGES = {
  python: { name: 'Python', extension: '.py', monacoLang: 'python' },
  javascript: { name: 'JavaScript', extension: '.js', monacoLang: 'javascript' },
  cpp: { name: 'C++', extension: '.cpp', monacoLang: 'cpp' },
  java: { name: 'Java', extension: '.java', monacoLang: 'java' },
};

// Default code templates
const DEFAULT_CODE = {
  python: `# Solution for the problem
def solve():
    # Read input
    n = int(input())
    
    # Your solution here
    pass

if __name__ == "__main__":
    solve()
`,
  javascript: `// Solution for the problem
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.on('line', (line) => {
  // Your solution here
});
`,
  cpp: `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    // Your solution here
    
    return 0;
}
`,
  java: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        
        // Your solution here
        
        sc.close();
    }
}
`,
};

// Mode configurations — only Coach (blue) and Rival (red)
const MODES = {
  blue: { name: 'Coach', color: 'bg-blue-500', textColor: 'text-white', description: 'Get hints and guidance' },
  red: { name: 'Rival', color: 'bg-red-500', textColor: 'text-white', description: 'Competitive mode with timer' },
};

// Timer presets
const TIMER_PRESETS = [
  { label: '15 min', minutes: 15 },
  { label: '30 min', minutes: 30 },
  { label: '45 min', minutes: 45 },
  { label: '1 hour', minutes: 60 },
  { label: '2 hours', minutes: 120 },
];

// Duck SVG Component
const DuckMascot = ({ mode, isAnimated }) => {
  const duckColor = mode === 'blue' ? '#3b82f6' : '#ef4444';
  const glowColor = mode === 'blue' ? 'rgba(59,130,246,0.5)' : 'rgba(239,68,68,0.5)';

  return (
    <div
      className={`relative transition-all duration-500 ${isAnimated ? 'animate-float' : ''}`}
      style={{ filter: `drop-shadow(0 0 20px ${glowColor})` }}
    >
      <svg viewBox="0 0 100 100" className="w-24 h-24">
        {/* Duck body */}
        <ellipse cx="50" cy="60" rx="30" ry="25" fill={duckColor} opacity="0.9" />
        {/* Duck head */}
        <circle cx="50" cy="35" r="20" fill={duckColor} opacity="0.9" />
        {/* Beak */}
        <ellipse cx="65" cy="38" rx="10" ry="5" fill="#f97316" />
        {/* Eye */}
        <circle cx="55" cy="32" r="4" fill="#1e293b" />
        <circle cx="56" cy="31" r="1.5" fill="white" />
        {/* Wing */}
        <ellipse cx="40" cy="60" rx="12" ry="15" fill={duckColor} opacity="0.7" />
        {/* Glasses for Coach mode */}
        {mode === 'blue' && (
          <>
            <circle cx="45" cy="32" r="8" fill="none" stroke="#1e293b" strokeWidth="2" />
            <circle cx="60" cy="32" r="8" fill="none" stroke="#1e293b" strokeWidth="2" />
            <line x1="53" y1="32" x2="52" y2="32" stroke="#1e293b" strokeWidth="2" />
          </>
        )}
        {/* Headband for Battle mode */}
        {mode === 'red' && (
          <>
            <rect x="30" y="25" width="40" height="5" fill="#dc2626" rx="2" />
            <polygon points="68,20 75,27 70,30 68,25" fill="#dc2626" />
          </>
        )}
      </svg>
    </div>
  );
};



// Main Workspace Component
export const Workspace = () => {
  const { contestId, problemIndex } = useParams();
  const navigate = useNavigate();
  const { user, idol, isAuthenticated, isLoading: isAuthLoading } = useAuth();

  // Problem state
  const [problem, setProblem] = useState(null);
  const [isLoadingProblem, setIsLoadingProblem] = useState(true);

  // UI state
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
  const [zenMode, setZenMode] = useState(false);
  const [currentMode, setCurrentMode] = useState('blue'); // blue, red
  const [leftPanelWidth, setLeftPanelWidth] = useState(320); // 320px = w-80
  const [rightPanelWidth, setRightPanelWidth] = useState(384); // 384px = w-96
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);

  // Timer state
  const [timerMinutes, setTimerMinutes] = useState(30);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [timerActive, setTimerActive] = useState(false);
  const [showTimerDropdown, setShowTimerDropdown] = useState(false);
  const timerRef = useRef(null);

  // Editor state — restore from localStorage if available
  const storageKey = `workspace_code_${contestId}_${problemIndex}`;
  const [files, setFiles] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.files && parsed.files.length > 0) return parsed.files;
      }
    } catch (e) { /* ignore */ }
    return [{ id: '1', name: 'solution', language: 'python', content: DEFAULT_CODE.python }];
  });
  const [activeFileId, setActiveFileId] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.activeFileId) return parsed.activeFileId;
      }
    } catch (e) { /* ignore */ }
    return '1';
  });
  const editorRef = useRef(null);

  // Terminal state
  const [terminalOutput, setTerminalOutput] = useState([
    { type: 'info', message: 'Ready to run your code...' }
  ]);
  const [isRunning, setIsRunning] = useState(false);

  // Chat state
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: "Hey there! 🦆 I'm your coding duck. How can I help you solve this problem?" }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatScrollRef = useRef(null);

  // Submit dialog state
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);

  // Get active file
  const activeFile = files.find(f => f.id === activeFileId) || files[0];

  // Fetch problem content
  useEffect(() => {
    const fetchProblem = async () => {
      if (!contestId || !problemIndex) return;

      setIsLoadingProblem(true);
      try {
        const response = await axios.get(`${BACKEND_URL}/api/problem/${contestId}/${problemIndex}`);
        setProblem(response.data);
      } catch (error) {
        console.error('Error fetching problem:', error);
        toast.error('Failed to load problem');
      } finally {
        setIsLoadingProblem(false);
      }
    };

    fetchProblem();
  }, [contestId, problemIndex]);

  // Timer effect
  useEffect(() => {
    if (timerActive && currentMode === 'red') {
      timerRef.current = setInterval(() => {
        setTimerSeconds(prev => {
          if (prev === 0) {
            setTimerMinutes(m => {
              if (m === 0) {
                clearInterval(timerRef.current);
                setTimerActive(false);
                toast.error("Time's up! ⏰");
                return 0;
              }
              return m - 1;
            });
            return 59;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [timerActive, currentMode]);

  // Scroll chat to bottom
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // Handle panel resizing
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizingLeft) {
        const newWidth = Math.max(200, Math.min(600, e.clientX));
        setLeftPanelWidth(newWidth);
      }
      if (isResizingRight) {
        const newWidth = Math.max(200, Math.min(600, window.innerWidth - e.clientX));
        setRightPanelWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizingLeft(false);
      setIsResizingRight(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizingLeft || isResizingRight) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingLeft, isResizingRight]);

  // Handle mode change
  const handleModeChange = (mode) => {
    setCurrentMode(mode);
    if (mode === 'red') {
      // Show timer dropdown to pick time (don't auto-start)
      if (!timerActive) {
        setShowTimerDropdown(true);
      }
    }
    // Don't stop timer when switching modes — timer persists
  };

  // Start timer
  const startTimer = (minutes) => {
    setTimerMinutes(minutes);
    setTimerSeconds(0);
    setTimerActive(true);
    setShowTimerDropdown(false);
    toast.success(`Rival mode activated! ${minutes} minutes on the clock.`);
  };

  // Pause/resume timer
  const toggleTimer = () => {
    if (timerActive) {
      setTimerActive(false);
      if (timerRef.current) clearInterval(timerRef.current);
      toast.info('Timer paused');
    } else if (timerMinutes > 0 || timerSeconds > 0) {
      setTimerActive(true);
      toast.info('Timer resumed');
    }
  };

  // Stop / reset timer
  const stopTimer = () => {
    setTimerActive(false);
    if (timerRef.current) clearInterval(timerRef.current);
    setTimerMinutes(30);
    setTimerSeconds(0);
  };

  // Handle editor mount
  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;

    // Set dark theme
    monaco.editor.defineTheme('idolcode-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#0a0f1a',
        'editor.foreground': '#e2e8f0',
        'editorLineNumber.foreground': '#4a5568',
        'editorCursor.foreground': '#06b6d4',
        'editor.selectionBackground': '#06b6d440',
      }
    });
    monaco.editor.setTheme('idolcode-dark');
  };

  // Handle code change — auto-save to localStorage
  const saveTimeoutRef = useRef(null);
  const handleCodeChange = (value) => {
    const updatedFiles = files.map(f =>
      f.id === activeFileId ? { ...f, content: value } : f
    );
    setFiles(updatedFiles);

    // Debounced auto-save (1 second)
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => {
      try {
        localStorage.setItem(storageKey, JSON.stringify({
          files: updatedFiles,
          activeFileId,
        }));
      } catch (e) { /* quota exceeded, ignore */ }
    }, 1000);
  };

  // Add new file
  const addNewFile = () => {
    const newId = String(Date.now());
    const newFile = {
      id: newId,
      name: `file${files.length + 1}`,
      language: 'python',
      content: DEFAULT_CODE.python
    };
    setFiles([...files, newFile]);
    setActiveFileId(newId);
  };

  // Change file language
  const changeFileLanguage = (fileId, language) => {
    setFiles(files.map(f =>
      f.id === fileId
        ? { ...f, language, content: DEFAULT_CODE[language] }
        : f
    ));
  };

  // Close file
  const closeFile = (fileId) => {
    if (files.length === 1) {
      toast.error('Cannot close the last file');
      return;
    }
    const newFiles = files.filter(f => f.id !== fileId);
    setFiles(newFiles);
    if (activeFileId === fileId) {
      setActiveFileId(newFiles[0].id);
    }
  };

  // Test code against sample test cases via backend
  const testCode = async () => {
    if (!problem?.examples?.length) {
      toast.error('No test cases available for this problem');
      return;
    }

    setIsRunning(true);
    setTerminalOutput([{ type: 'info', message: '▶ Running tests against sample cases...' }]);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/test-code`, {
        code: activeFile.content,
        language: activeFile.language,
        testCases: problem.examples.map(ex => ({
          input: ex.input,
          output: ex.output,
        })),
      });

      const { results, allPassed } = response.data;

      const output = results.map(r => ({
        type: r.passed ? 'success' : 'error',
        message: `Test ${r.testCase}: ${r.passed ? '✓ PASSED' : '✗ WRONG ANSWER'}\n  Input: ${r.input.substring(0, 80)}\n  Expected: ${r.expected.substring(0, 80)}\n  Got: ${r.actual.substring(0, 80)}`,
      }));

      output.push({
        type: allPassed ? 'success' : 'error',
        message: allPassed
          ? '═══════════════════════════════\n  ALL TESTS PASSED! ✓\n═══════════════════════════════'
          : '═══════════════════════════════\n  SOME TESTS FAILED ✗\n═══════════════════════════════',
      });

      setTerminalOutput([{ type: 'info', message: '▶ Running tests against sample cases...' }, ...output]);

      if (allPassed) toast.success('All sample tests passed! 🎉');
      else toast.error('Some tests failed');
    } catch (error) {
      const detail = error.response?.data?.detail || error.message;
      setTerminalOutput([
        { type: 'info', message: '▶ Running tests against sample cases...' },
        { type: 'error', message: `Error: ${detail}` },
      ]);
      toast.error('Test execution failed');
    } finally {
      setIsRunning(false);
    }
  };

  // Handle chat submit — real Gemini-powered Duck Chat
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    if (currentMode === 'red') {
      toast.error('Chat is locked in Rival mode!');
      return;
    }

    const userMessage = chatInput.trim();
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/duck-chat`, {
        message: userMessage,
        problemTitle: problem?.title || '',
        problemStatement: problem?.statement || '',
        code: activeFile?.content || '',
        language: activeFile?.language || '',
        idolHandle: idol?.handle || '',
        chatHistory: chatMessages.slice(-10),
      });

      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.reply,
      }]);
    } catch (error) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Quack! 🦆 Something went wrong. Please try again.',
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Handle submit — open Codeforces submission page
  const handleSubmit = () => {
    // Save code to localStorage before showing dialog
    try {
      localStorage.setItem(storageKey, JSON.stringify({ files, activeFileId }));
    } catch (e) { /* ignore */ }
    setShowSubmitDialog(true);
  };

  const confirmSubmit = () => {
    setShowSubmitDialog(false);
    // Open Codeforces submission page in new tab
    const cfSubmitUrl = `https://codeforces.com/contest/${contestId}/submit/${problemIndex}`;
    window.open(cfSubmitUrl, '_blank');
    toast.success('Opening Codeforces submission page — paste your solution there!');
  };

  // Loading state
  if (isAuthLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Top Navigation Bar */}
      <div className="h-12 bg-card border-b border-border flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
            className="hover:bg-primary/10"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <span className="text-sm text-muted-foreground">
            Problem: <span className="text-primary font-mono">{contestId}{problemIndex}</span>
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Timer (visible only in red mode) */}
          {currentMode === 'red' && (
            <div className={`flex items-center gap-2 px-3 py-1 rounded-lg ${timerActive ? 'bg-red-500/20 border border-red-500/30' : 'bg-muted/50'}`}>
              <Timer className={`w-4 h-4 ${timerActive ? 'text-red-400' : 'text-muted-foreground'}`} />
              <span className={`font-mono text-sm ${timerActive ? 'text-red-400' : 'text-muted-foreground'}`}>
                {String(timerMinutes).padStart(2, '0')}:{String(timerSeconds).padStart(2, '0')}
              </span>

              {/* Pause / Resume toggle */}
              {(timerActive || (timerMinutes > 0 || timerSeconds > 0)) && (timerMinutes !== 30 || timerSeconds !== 0 || timerActive) && (
                <button onClick={toggleTimer} className="p-1 hover:bg-muted rounded" title={timerActive ? 'Pause' : 'Resume'}>
                  {timerActive ? <Pause className="w-3 h-3 text-red-400" /> : <Play className="w-3 h-3 text-muted-foreground" />}
                </button>
              )}

              {/* Timer preset dropdown (when not active) */}
              <DropdownMenu open={showTimerDropdown} onOpenChange={setShowTimerDropdown}>
                <DropdownMenuTrigger asChild>
                  <button className="p-1 hover:bg-muted rounded">
                    <ChevronDown className="w-3 h-3" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {TIMER_PRESETS.map((preset) => (
                    <DropdownMenuItem key={preset.minutes} onClick={() => startTimer(preset.minutes)}>
                      <Clock className="w-4 h-4 mr-2" />
                      {preset.label}
                    </DropdownMenuItem>
                  ))}
                  {timerActive && (
                    <DropdownMenuItem onClick={stopTimer} className="text-red-400">
                      <X className="w-4 h-4 mr-2" />
                      Stop Timer
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}

          {/* Zen Mode Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZenMode(!zenMode)}
            className={`transition-all ${zenMode ? 'bg-primary/20 text-primary shadow-[0_0_15px_rgba(6,182,212,0.5)]' : 'hover:bg-primary/10'}`}
          >
            <Moon className="w-4 h-4" />
          </Button>


          {/* Test Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={testCode}
            disabled={isRunning}
            className="hover:bg-blue-500/10 hover:text-blue-400"
          >
            <FlaskConical className="w-4 h-4 mr-1" />
            Test
          </Button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Problem & Visualizer */}
        {!zenMode && (
          <div
            className="border-r border-border flex flex-col"
            style={{
              width: leftPanelCollapsed ? 0 : `${leftPanelWidth}px`,
              overflow: leftPanelCollapsed ? 'hidden' : 'visible',
              transition: leftPanelCollapsed ? 'width 0.3s' : 'none'
            }}
          >
            {/* Problem Description */}
            <div className="flex-1 flex flex-col min-h-0">
              <div className="h-10 bg-card/50 border-b border-border flex items-center justify-between px-3">
                <span className="text-sm font-medium text-foreground flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-primary" />
                  Problem
                </span>
                <a
                  href={problem?.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary hover:text-primary transition-all text-sm font-medium border border-primary/20 hover:border-primary/30"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  View on Codeforces
                </a>
              </div>

              <ScrollArea className="flex-1">
                {isLoadingProblem ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  </div>
                ) : problem ? (
                  <div className="p-4 space-y-4 text-sm">
                    <div>
                      <h2 className="text-lg font-bold text-foreground mb-1">{problem.name}</h2>
                      <div className="flex gap-2 text-xs text-muted-foreground">
                        <span>{problem.timeLimit}</span>
                        <span>•</span>
                        <span>{problem.memoryLimit}</span>
                        {problem.rating && (
                          <>
                            <span>•</span>
                            <span className="text-primary">Rating: {problem.rating}</span>
                          </>
                        )}
                      </div>
                    </div>

                    {problem.tags?.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {problem.tags.map((tag, i) => (
                          <span key={i} className="px-2 py-0.5 text-xs rounded-full bg-secondary/50 text-muted-foreground">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="prose prose-sm prose-invert max-w-none">
                      <LatexRenderer text={problem.problemStatement} className="text-muted-foreground" />

                      {problem.inputSpecification && (
                        <div className="mt-4">
                          <h4 className="text-sm font-semibold text-foreground">Input</h4>
                          <LatexRenderer text={problem.inputSpecification} className="text-muted-foreground" />
                        </div>
                      )}

                      {problem.outputSpecification && (
                        <div className="mt-4">
                          <h4 className="text-sm font-semibold text-foreground">Output</h4>
                          <LatexRenderer text={problem.outputSpecification} className="text-muted-foreground" />
                        </div>
                      )}

                      {problem.examples?.length > 0 && (
                        <div className="mt-4">
                          <h4 className="text-sm font-semibold text-foreground mb-2">Examples</h4>
                          {problem.examples.map((ex, i) => (
                            <div key={i} className="mb-3 rounded-lg overflow-hidden border border-border">
                              <div className="bg-muted/50 px-3 py-1 text-xs text-muted-foreground">
                                Input
                              </div>
                              <pre className="px-3 py-2 text-xs font-mono bg-card/30 overflow-x-auto">
                                {ex.input}
                              </pre>
                              <div className="bg-muted/50 px-3 py-1 text-xs text-muted-foreground border-t border-border">
                                Output
                              </div>
                              <pre className="px-3 py-2 text-xs font-mono bg-card/30 overflow-x-auto">
                                {ex.output}
                              </pre>
                            </div>
                          ))}
                        </div>
                      )}

                      {problem.note && (
                        <div className="mt-4">
                          <h4 className="text-sm font-semibold text-foreground">Note</h4>
                          <LatexRenderer text={problem.note} className="text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    Problem not found
                  </div>
                )}
              </ScrollArea>
            </div>
          </div>
        )}

        {/* Resize Handle for Left Panel */}
        {!zenMode && !leftPanelCollapsed && (
          <div
            onMouseDown={() => setIsResizingLeft(true)}
            className="w-1 bg-border hover:bg-primary/50 cursor-col-resize transition-colors flex items-center justify-center group relative"
          >
            <div className="absolute w-4 h-full" /> {/* Wider hit area */}
            <div className="w-0.5 h-8 bg-muted-foreground/30 group-hover:bg-primary/70 rounded-full transition-colors" />
          </div>
        )}

        {/* Collapse Toggle */}
        {!zenMode && (
          <button
            onClick={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
            className="w-4 bg-card hover:bg-muted flex items-center justify-center border-r border-border transition-colors"
          >
            {leftPanelCollapsed ? (
              <ChevronRight className="w-3 h-3 text-muted-foreground" />
            ) : (
              <ChevronLeft className="w-3 h-3 text-muted-foreground" />
            )}
          </button>
        )}

        {/* Middle Panel - Editor & Terminal */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* File Tabs */}
          <div className="h-10 bg-card/50 border-b border-border flex items-center px-2 gap-1">
            {files.map((file) => (
              <div
                key={file.id}
                className={`group flex items-center gap-2 px-3 py-1.5 rounded-t-lg cursor-pointer transition-all ${file.id === activeFileId
                  ? 'bg-background border-t border-l border-r border-border text-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                  }`}
                onClick={() => setActiveFileId(file.id)}
              >
                <FileCode className="w-3 h-3" />
                <span className="text-xs">{file.name}{LANGUAGES[file.language].extension}</span>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="p-0.5 hover:bg-muted rounded opacity-0 group-hover:opacity-100 transition-opacity">
                      <ChevronDown className="w-3 h-3" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    {Object.entries(LANGUAGES).map(([key, lang]) => (
                      <DropdownMenuItem key={key} onClick={() => changeFileLanguage(file.id, key)}>
                        {lang.name}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
                {files.length > 1 && (
                  <button
                    className="p-0.5 hover:bg-destructive/20 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => { e.stopPropagation(); closeFile(file.id); }}
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}

            {/* Add File Button */}
            <button
              onClick={addNewFile}
              className="p-1.5 hover:bg-muted rounded-lg transition-colors text-muted-foreground hover:text-foreground"
            >
              <Plus className="w-4 h-4" />
            </button>

            {/* Import Button */}
            <button
              onClick={() => toast.info('Import feature coming soon!')}
              className="p-1.5 hover:bg-muted rounded-lg transition-colors text-muted-foreground hover:text-foreground ml-auto"
            >
              <Upload className="w-4 h-4" />
            </button>
          </div>

          {/* Code Editor */}
          <div className="flex-1 min-h-0">
            <Editor
              height="100%"
              language={LANGUAGES[activeFile.language].monacoLang}
              value={activeFile.content}
              onChange={handleCodeChange}
              onMount={handleEditorDidMount}
              options={{
                fontSize: 14,
                fontFamily: 'JetBrains Mono, Fira Code, monospace',
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                lineNumbers: 'on',
                renderLineHighlight: 'line',
                cursorBlinking: 'smooth',
                cursorSmoothCaretAnimation: 'on',
                smoothScrolling: true,
                padding: { top: 16 },
              }}
              theme="vs-dark"
            />
          </div>

          {/* Terminal */}
          <div className="h-40 border-t border-border flex flex-col">
            <div className="h-8 bg-card/50 border-b border-border flex items-center px-3">
              <span className="text-xs font-medium text-muted-foreground">Terminal</span>
              {isRunning && <Loader2 className="w-3 h-3 animate-spin ml-2 text-primary" />}
            </div>
            <ScrollArea className="flex-1 bg-[#0a0f1a]">
              <div className="p-3 font-mono text-xs space-y-1">
                {terminalOutput.map((line, i) => (
                  <div
                    key={i}
                    className={`whitespace-pre-wrap ${line.type === 'error' ? 'text-red-400' :
                      line.type === 'success' ? 'text-green-400' :
                        line.type === 'output' ? 'text-blue-300' :
                          'text-muted-foreground'
                      }`}
                  >
                    {line.message}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* Resize Handle for Right Panel */}
        {!zenMode && (
          <div
            onMouseDown={() => setIsResizingRight(true)}
            className="w-1 bg-border hover:bg-primary/50 cursor-col-resize transition-colors flex items-center justify-center group relative"
          >
            <div className="absolute w-4 h-full" /> {/* Wider hit area */}
            <div className="w-0.5 h-8 bg-muted-foreground/30 group-hover:bg-primary/70 rounded-full transition-colors" />
          </div>
        )}

        {/* Right Panel - Duck & Chat */}
        {!zenMode && (
          <div
            className="border-l border-border flex flex-col"
            style={{ width: `${rightPanelWidth}px` }}
          >
            {/* Mode Buttons & Duck */}
            <div className="p-4 border-b border-border">
              {/* Mode Buttons */}
              <div className="flex justify-center gap-3 mb-4">
                {Object.entries(MODES).map(([key, mode]) => (
                  <button
                    key={key}
                    onClick={() => handleModeChange(key)}
                    className={`w-12 h-12 rounded-xl transition-all ${mode.color} ${currentMode === key
                      ? 'ring-2 ring-offset-2 ring-offset-background ring-primary shadow-lg scale-110'
                      : 'opacity-70 hover:opacity-100'
                      }`}
                    title={mode.description}
                  >
                    {key === 'blue' && <Sparkles className="w-5 h-5 mx-auto text-white" />}
                    {key === 'red' && <Swords className="w-5 h-5 mx-auto text-white" />}
                  </button>
                ))}
              </div>

              {/* Duck Mascot */}
              <div className="flex flex-col items-center">
                <DuckMascot mode={currentMode} isAnimated={true} />
                <p className="text-xs text-muted-foreground mt-2">
                  {MODES[currentMode].name} Mode
                </p>
              </div>
            </div>

            {/* Chat Section */}
            <div className="flex-1 flex flex-col min-h-0">
              <div className="h-8 bg-card/50 border-b border-border flex items-center px-3">
                <MessageCircle className="w-3 h-3 mr-2 text-primary" />
                <span className="text-xs font-medium text-muted-foreground">
                  {currentMode === 'red' ? 'Chat Locked (Rival Mode)' : 'Duck Chat'}
                </span>
                {isChatLoading && <Loader2 className="w-3 h-3 animate-spin ml-2 text-primary" />}
              </div>

              {currentMode === 'red' ? (
                <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground gap-2">
                  <Lock className="w-6 h-6" />
                  <span className="text-sm font-medium">Rival Mode — Focus!</span>
                  <span className="text-xs text-muted-foreground/70">No hints available</span>
                </div>
              ) : (
                <>
                  <ScrollArea className="flex-1" ref={chatScrollRef}>
                    <div className="p-3 space-y-3">
                      {chatMessages.map((msg, i) => (
                        <div
                          key={i}
                          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[85%] px-3 py-2 rounded-2xl text-sm ${msg.role === 'user'
                              ? 'bg-primary text-primary-foreground rounded-br-sm'
                              : 'bg-muted text-foreground rounded-bl-sm'
                              }`}
                          >
                            {msg.content}
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>

                  <form onSubmit={handleChatSubmit} className="p-3 border-t border-border">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="Ask the duck..."
                        className="flex-1 bg-muted/50 border border-border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                      <Button type="submit" size="sm" className="rounded-xl">
                        <Send className="w-4 h-4" />
                      </Button>
                    </div>
                  </form>
                </>
              )}
            </div>

            {/* Submit Button */}
            <div className="p-4 border-t border-border">
              <Button
                onClick={handleSubmit}
                className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold"
              >
                <Send className="w-4 h-4 mr-2" />
                Submit Solution
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Submit Confirmation Dialog */}
      <AlertDialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
        <AlertDialogContent className="glass-card border-border">
          <AlertDialogHeader>
            <AlertDialogTitle>Submit to Codeforces</AlertDialogTitle>
            <AlertDialogDescription>
              Go to Codeforces submission page? You can paste your solution there to submit.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction onClick={confirmSubmit}>
              OK
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Workspace;
