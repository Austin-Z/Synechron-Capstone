import React from 'react';
import { toast } from 'sonner';
import { Button } from "../components/ui/button";
import { ArrowRight, BarChart3, ChevronRight, CreditCard, Lock, LineChart, ShieldCheck, Users } from "lucide-react";
import FeatureCard from "../components/FeatureCard";
import TestimonialCard from "../components/TestimonialCard";

const Index: React.FC = () => {
  // State to track the active screenshot
  const [activeScreenshot, setActiveScreenshot] = React.useState(0);
  const totalScreenshots = 4; // Total number of screenshots in the carousel

  // Function to cycle to the next screenshot
  const nextScreenshot = () => {
    setActiveScreenshot((prev) => (prev + 1) % totalScreenshots);
  };

  // Function to cycle to the previous screenshot
  const prevScreenshot = () => {
    setActiveScreenshot((prev) => (prev - 1 + totalScreenshots) % totalScreenshots);
  };

  // Function to handle demo button click - this will redirect to the Streamlit dashboard
  const handleDemoClick = () => {
    toast.loading('Loading dashboard...', {
      description: 'Preparing your interactive data experience',
      duration: 2000,
    });
    
    // Determine if we're in local development or production environment
    const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    // Simulate loading and then navigate to the Streamlit dashboard
    setTimeout(() => {
      if (isLocalDev) {
        // For local development, navigate directly to the Streamlit server
        window.location.href = 'http://localhost:8501/dashboard';
      } else {
        // For production deployment, use a relative path that will be handled by Nginx
        window.location.href = '/dashboard';
      }
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-[#111827] text-white overflow-hidden">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 md:py-32 flex flex-col items-center text-center relative">
        {/* Background decorative elements */}
        <div className="absolute top-20 left-10 w-64 h-64 bg-blue-900 rounded-full filter blur-3xl opacity-20 animate-float"></div>
        <div className="absolute bottom-20 right-10 w-80 h-80 bg-indigo-900 rounded-full filter blur-3xl opacity-20" style={{animationDelay: '1s'}}></div>
        
        <div className="mb-8 relative z-10">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-gray-300 mb-2">
            <span className="inline-block">Fund-of-Funds</span>
          </h1>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-gray-300">
            <span className="inline-block">Intelligence</span>
          </h1>
        </div>
        
        <p className="mt-6 text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto relative z-10 leading-relaxed">
          AI-powered analytics platform for visualizing fund structures, detecting overlaps, and optimizing portfolio performance.
        </p>
        <div className="mt-12 flex flex-col sm:flex-row gap-6 justify-center relative z-10">
          <Button 
            onClick={handleDemoClick}
            size="lg" 
            className="bg-blue-600 hover:bg-blue-700 text-white px-10 py-6 text-lg rounded-md transition-all duration-300"
          >
            See Demo <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
          <Button variant="outline" size="lg" className="border-gray-700 text-gray-300 hover:bg-gray-800 hover:border-gray-600 px-10 py-6 text-lg rounded-md transition-all duration-300">
            Learn More <ChevronRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </section>

      {/* Trusted By Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <div className="text-center mb-10">
          <h2 className="text-xl font-medium text-gray-400">Trusted by leading financial institutions</h2>
        </div>
        <div className="flex flex-wrap justify-center items-center gap-10 md:gap-20">
          <div className="h-10 px-4 bg-gray-800 rounded-lg opacity-60 hover:opacity-100 transition-opacity duration-300 flex items-center justify-center text-gray-300 font-medium">BlackRock</div>
          <div className="h-10 px-4 bg-gray-800 rounded-lg opacity-60 hover:opacity-100 transition-opacity duration-300 flex items-center justify-center text-gray-300 font-medium">Vanguard</div>
          <div className="h-10 px-4 bg-gray-800 rounded-lg opacity-60 hover:opacity-100 transition-opacity duration-300 flex items-center justify-center text-gray-300 font-medium">Fidelity</div>
          <div className="h-10 px-4 bg-gray-800 rounded-lg opacity-60 hover:opacity-100 transition-opacity duration-300 flex items-center justify-center text-gray-300 font-medium">State Street</div>
          <div className="h-10 px-4 bg-gray-800 rounded-lg opacity-60 hover:opacity-100 transition-opacity duration-300 flex items-center justify-center text-gray-300 font-medium">JPMorgan</div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container mx-auto px-4 py-20 md:py-32 relative">
        {/* Background decorative element */}
        <div className="absolute top-1/2 right-0 w-96 h-96 bg-blue-900 rounded-full filter blur-3xl opacity-10"></div>
        
        <div className="text-center mb-20 relative z-10">
          <h2 className="text-4xl md:text-5xl font-bold text-white">Powerful Features</h2>
          <p className="mt-6 text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Comprehensive tools for fund-of-funds analysis and optimization
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 relative z-10">
          <FeatureCard 
            icon={<LineChart className="h-10 w-10 text-blue-500" />}
            title="Advanced Analytics"
            description="Visualize fund structures, detect overlaps, and analyze asset allocations with interactive heatmaps and correlation matrices."
          />
          <FeatureCard 
            icon={<svg className="h-10 w-10 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>}
            title="AI-Powered Insights"
            description="Leverage Gemini 2.0 Flash API to get intelligent answers about funds, holdings, and investment strategies."
          />
          <FeatureCard 
            icon={<svg className="h-10 w-10 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>}
            title="Interactive Dashboards"
            description="Explore fund data through customizable, interactive visualizations including Sankey diagrams, heatmaps, and allocation charts."
          />
          <FeatureCard 
            icon={<BarChart3 className="h-10 w-10 text-blue-500" />}
            title="Performance Reports"
            description="Generate detailed reports on fund performance, holdings distribution, and investment growth metrics with visual correlation heatmaps."
          />
          <FeatureCard 
            icon={<svg className="h-10 w-10 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>}
            title="Optimization Algorithms"
            description="Identify optimal portfolio allocations and reduce redundant holdings with advanced optimization algorithms and correlation analysis."
          />
          <FeatureCard 
            icon={<svg className="h-10 w-10 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>}
            title="Automated Data Updates"
            description="Stay current with automatic SEC EDGAR data collection and processing for the latest fund holdings and filings."
          />
        </div>
      </section>
      
      {/* How It Works Section */}
      <section id="how-it-works" className="container mx-auto px-4 py-20 md:py-32">
        <div className="bg-gray-800/90 backdrop-blur-sm rounded-md shadow-xl p-12 relative overflow-hidden">
          {/* Background decorative elements */}
          <div className="absolute top-0 left-0 w-64 h-64 bg-blue-900 rounded-full filter blur-3xl opacity-10"></div>
          <div className="absolute bottom-0 right-0 w-64 h-64 bg-indigo-900 rounded-full filter blur-3xl opacity-10"></div>
          
          <div className="text-center mb-20 relative z-10">
            <h2 className="text-4xl md:text-5xl font-bold text-white">How It Works</h2>
            <p className="mt-6 text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
              Three simple steps to optimize your fund-of-funds portfolio
            </p>
          </div>
          
          <div className="flex flex-col md:flex-row gap-16 items-center relative z-10">
            <div className="flex-1 order-2 md:order-1">
              <div className="space-y-10">
                <div className="flex gap-6 items-start group hover:translate-x-1 transition-transform duration-300">
                  <div className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-full p-4 mt-1 shadow-md group-hover:shadow-lg transition-shadow duration-300">
                    <span className="text-xl font-bold">1</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors duration-300">Create an account</h3>
                    <p className="mt-3 text-lg text-gray-300 leading-relaxed">Sign up with your email to access the full suite of fund analysis tools</p>
                  </div>
                </div>
                
                <div className="flex gap-6 items-start group hover:translate-x-1 transition-transform duration-300">
                  <div className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-full p-4 mt-1 shadow-md group-hover:shadow-lg transition-shadow duration-300">
                    <span className="text-xl font-bold">2</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors duration-300">Upload your portfolio</h3>
                    <p className="mt-3 text-lg text-gray-300 leading-relaxed">Import your fund holdings or select from our database of thousands of funds</p>
                  </div>
                </div>
                
                <div className="flex gap-6 items-start group hover:translate-x-1 transition-transform duration-300">
                  <div className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-full p-4 mt-1 shadow-md group-hover:shadow-lg transition-shadow duration-300">
                    <span className="text-xl font-bold">3</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors duration-300">Analyze and optimize</h3>
                    <p className="mt-3 text-lg text-gray-300 leading-relaxed">Discover overlapping holdings, identify redundancies, and optimize your portfolio</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex-1 order-1 md:order-2">
              <div className="relative h-96 perspective-1000">
                {/* Screenshot carousel */}
                <div className="relative h-full w-full">
                  {/* Screenshot 1 */}
                  <div 
                    className={`absolute inset-0 transition-all duration-500 ${activeScreenshot === 0 ? 'opacity-100 z-10 transform-none' : 
                      activeScreenshot === 1 ? 'opacity-0 -translate-x-full' : 
                      activeScreenshot === 3 ? 'opacity-0 translate-x-full' : 'opacity-0'}`}
                  >
                    <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-md h-full w-full shadow-xl overflow-hidden relative">
                      {/* Fund Overlap Screenshot */}
                      <div className="absolute inset-0 flex items-center justify-center overflow-hidden bg-[#111827]">
                        <img 
                          src="/screenshots/fund-overlap.png" 
                          alt="Fund Overlap Visualization" 
                          className="w-full h-full object-contain"
                        />
                      </div>
                      

                    </div>
                  </div>
                  
                  {/* Screenshot 2 */}
                  <div 
                    className={`absolute inset-0 transition-all duration-500 ${activeScreenshot === 1 ? 'opacity-100 z-10 transform-none' : 
                      activeScreenshot === 2 ? 'opacity-0 -translate-x-full' : 
                      activeScreenshot === 0 ? 'opacity-0 translate-x-full' : 'opacity-0'}`}
                  >
                    <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-md h-full w-full shadow-xl overflow-hidden">
                      <div className="h-full w-full flex items-center justify-center overflow-hidden bg-[#111827]">
                        <img 
                          src="/screenshots/portfolio-viz.png" 
                          alt="Portfolio Visualization" 
                          className="w-full h-full object-contain"
                        />
                      </div>
                    </div>
                  </div>
                  
                  {/* Screenshot 3 - AI Chat Interface */}
                  <div 
                    className={`absolute inset-0 transition-all duration-500 ${activeScreenshot === 2 ? 'opacity-100 z-10 transform-none' : 
                      activeScreenshot === 3 ? 'opacity-0 -translate-x-full' : 
                      activeScreenshot === 1 ? 'opacity-0 translate-x-full' : 'opacity-0'}`}
                  >
                    <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-md h-full w-full shadow-xl overflow-hidden">
                      {/* AI Chat Screenshot */}
                      <div className="absolute inset-0 flex items-center justify-center overflow-hidden bg-[#111827]">
                        <img 
                          src="/screenshots/ai-chat.png" 
                          alt="AI Chat Interface" 
                          className="w-full h-full object-contain"
                        />
                      </div>
                      

                    </div>
                  </div>

                  {/* Screenshot 4 */}
                  <div 
                    className={`absolute inset-0 transition-all duration-500 ${activeScreenshot === 3 ? 'opacity-100 z-10 transform-none' : 
                      activeScreenshot === 0 ? 'opacity-0 -translate-x-full' : 
                      activeScreenshot === 2 ? 'opacity-0 translate-x-full' : 'opacity-0'}`}
                  >
                    <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-md h-full w-full shadow-xl overflow-hidden">
                      <div className="h-full w-full flex items-center justify-center overflow-hidden bg-[#111827]">
                        <img 
                          src="/screenshots/holding-breakdown.png" 
                          alt="Holdings Breakdown" 
                          className="w-full h-full object-contain"
                        />
                      </div>
                    </div>
                  </div>



                  {/* Navigation buttons */}
                  <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 flex justify-between z-20 px-4">
                    <button 
                      onClick={prevScreenshot}
                      className="bg-gray-800/80 hover:bg-gray-700/80 text-white rounded-full p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                      aria-label="Previous screenshot"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                      </svg>
                    </button>
                    <button 
                      onClick={nextScreenshot}
                      className="bg-gray-800/80 hover:bg-gray-700/80 text-white rounded-full p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                      aria-label="Next screenshot"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>

                  {/* Indicator dots */}
                  <div className="absolute bottom-4 inset-x-0 flex justify-center gap-2 z-20">
                    {Array.from({ length: totalScreenshots }).map((_, index) => (
                      <button
                        key={index}
                        onClick={() => setActiveScreenshot(index)}
                        className={`h-2 w-2 rounded-full transition-all ${activeScreenshot === index ? 'bg-blue-500 w-4' : 'bg-gray-500 hover:bg-gray-400'}`}
                        aria-label={`Go to screenshot ${index + 1}`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="container mx-auto px-4 py-20 md:py-32 relative">
        {/* Background decorative element */}
        <div className="absolute top-1/3 left-0 w-96 h-96 bg-indigo-900 rounded-full filter blur-3xl opacity-10"></div>
        
        <div className="text-center mb-20 relative z-10">
          <h2 className="text-4xl md:text-5xl font-bold text-white">What Our Clients Say</h2>
          <p className="mt-6 text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Trusted by thousands of financial professionals worldwide
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10 relative z-10">
          <TestimonialCard 
            quote="This platform has completely transformed how we analyze market data. The insights are invaluable."
            author="Sarah Johnson"
            role="Investment Analyst, ABC Capital"
          />
          <TestimonialCard 
            quote="The security features give us peace of mind when handling sensitive financial information."
            author="Michael Chen"
            role="CFO, XYZ Enterprises"
          />
          <TestimonialCard 
            quote="Implementing this solution has increased our efficiency by 40% and reduced errors by 90%."
            author="Emily Rodriguez"
            role="Financial Director, Global Finance"
          />
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="container mx-auto px-4 py-20 md:py-32 relative">
        {/* Background decorative element */}
        <div className="absolute top-1/3 right-0 w-96 h-96 bg-blue-900 rounded-full filter blur-3xl opacity-10"></div>
        
        <div className="text-center mb-20 relative z-10">
          <h2 className="text-4xl md:text-5xl font-bold text-white">Simple, Transparent Pricing</h2>
          <p className="mt-6 text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Choose the plan that works best for your business
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
          {/* Basic Plan */}
          <div className="bg-gray-800/90 border border-gray-700 rounded-md overflow-hidden hover:shadow-xl transition-all duration-300">
            <div className="p-8">
              <h3 className="text-2xl font-bold text-white mb-4">Starter</h3>
              <div className="flex items-end mb-6">
                <span className="text-4xl font-bold text-white">$29</span>
                <span className="text-gray-400 ml-2">/month</span>
              </div>
              <p className="text-gray-300 mb-6">Perfect for individuals and small teams just getting started</p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> Basic analytics
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> 5 user accounts
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> 1GB storage
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> Email support
                </li>
              </ul>
              <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-md">
                Get Started
              </Button>
            </div>
          </div>
          
          {/* Pro Plan */}
          <div className="bg-gray-800/90 border border-blue-600 rounded-md overflow-hidden hover:shadow-xl transition-all duration-300 transform scale-105">
            <div className="bg-blue-600 text-white text-center py-2 text-sm font-medium">
              MOST POPULAR
            </div>
            <div className="p-8">
              <h3 className="text-2xl font-bold text-white mb-4">Professional</h3>
              <div className="flex items-end mb-6">
                <span className="text-4xl font-bold text-white">$79</span>
                <span className="text-gray-400 ml-2">/month</span>
              </div>
              <p className="text-gray-300 mb-6">Ideal for growing businesses with more advanced needs</p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> Advanced analytics
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> 20 user accounts
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> 10GB storage
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> Priority support
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> API access
                </li>
              </ul>
              <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-md">
                Get Started
              </Button>
            </div>
          </div>
          
          {/* Enterprise Plan */}
          <div className="bg-gray-800/90 border border-gray-700 rounded-md overflow-hidden hover:shadow-xl transition-all duration-300">
            <div className="p-8">
              <h3 className="text-2xl font-bold text-white mb-4">Enterprise</h3>
              <div className="flex items-end mb-6">
                <span className="text-4xl font-bold text-white">$199</span>
                <span className="text-gray-400 ml-2">/month</span>
              </div>
              <p className="text-gray-300 mb-6">For large organizations with complex requirements</p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> Custom analytics
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> Unlimited users
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> 100GB storage
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> 24/7 phone support
                </li>
                <li className="flex items-center text-gray-300">
                  <span className="mr-2 text-blue-500">✓</span> Custom integrations
                </li>
              </ul>
              <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-md">
                Contact Sales
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 md:py-32">
        <div className="bg-gradient-to-r from-blue-800 to-indigo-900 rounded-md py-20 px-12 text-center text-white shadow-2xl relative overflow-hidden border border-gray-700">
          {/* Background decorative elements */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full filter blur-3xl"></div>
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-white/5 rounded-full filter blur-3xl"></div>
          
          <h2 className="text-4xl md:text-5xl font-bold relative z-10">Ready to transform your financial operations?</h2>
          <p className="mt-6 text-xl md:text-2xl max-w-3xl mx-auto text-gray-300 leading-relaxed relative z-10">
            Experience the power and simplicity of our financial platform firsthand with an interactive demo.
          </p>
          <Button 
            onClick={handleDemoClick}
            size="lg" 
            className="mt-10 bg-blue-600 hover:bg-blue-700 text-white shadow-xl px-10 py-6 text-lg rounded-md transition-all duration-300 relative z-10"
          >
            See Demo <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </section>
    </div>
  );
};

export default Index;
