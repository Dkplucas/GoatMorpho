import { useState, useEffect } from "react";
import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import Home from "@/pages/home";
import LoginPage from "@/pages/login";
import WelcomePage from "@/pages/welcome";

type AuthState = "loading" | "authenticated" | "unauthenticated" | "welcome";

function Router({ authState, onLogin, onShowLogin }: { 
  authState: AuthState; 
  onLogin: () => void; 
  onShowLogin: () => void;
}) {
  if (authState === "loading") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-agri-green mx-auto mb-4"></div>
          <p className="text-agri-gray">Loading...</p>
        </div>
      </div>
    );
  }

  if (authState === "welcome") {
    return <WelcomePage onGetStarted={onShowLogin} />;
  }

  if (authState === "unauthenticated") {
    return <LoginPage onLoginSuccess={onLogin} />;
  }

  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  const [authState, setAuthState] = useState<AuthState>("loading");

  useEffect(() => {
    // Check if user has visited before (simple localStorage check)
    const hasVisitedBefore = localStorage.getItem("hasVisitedBefore");
    
    // For demo purposes, we'll show the welcome page first
    // In a real app, you'd check for existing authentication tokens
    setTimeout(() => {
      if (!hasVisitedBefore) {
        setAuthState("welcome");
        localStorage.setItem("hasVisitedBefore", "true");
      } else {
        setAuthState("unauthenticated");
      }
    }, 1000);
  }, []);

  const handleLogin = () => {
    setAuthState("authenticated");
  };

  const handleShowLogin = () => {
    setAuthState("unauthenticated");
  };

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router 
          authState={authState} 
          onLogin={handleLogin} 
          onShowLogin={handleShowLogin}
        />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
