import { useState } from "react";
import { Link } from 'react-router-dom';
import { Button } from "./ui/button";
import { Menu, X } from "lucide-react";

const NavBar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="bg-[#111827] backdrop-blur-md sticky top-0 z-50 border-b border-gray-800">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex-shrink-0 font-bold text-white flex items-center">
            <span className="text-5xl font-bold text-blue-500">BiL</span>
          </Link>
          
          {/* Desktop menu */}
          <div className="hidden md:flex items-center space-x-6">
            <a href="#features" className="text-gray-300 hover:text-white px-3 py-2 text-base font-medium">Features</a>
            <a href="#how-it-works" className="text-gray-300 hover:text-white px-3 py-2 text-base font-medium">How It Works</a>
            <a href="#pricing" className="text-gray-300 hover:text-white px-3 py-2 text-base font-medium">Pricing</a>
            <a href="#testimonials" className="text-gray-300 hover:text-white px-3 py-2 text-base font-medium">Testimonials</a>
          </div>
          
          <div className="hidden md:flex items-center space-x-3">
            <Button 
              variant="ghost" 
              className="text-gray-300 hover:text-white border-none text-base"
              onClick={() => window.location.href = '/login'}
            >
              Log in
            </Button>
            <Button 
              variant="default" 
              className="bg-blue-600 hover:bg-blue-700 text-white text-base"
              onClick={() => window.location.href = '/dashboard'}
            >
              Sign up
            </Button>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMenuOpen ? <X /> : <Menu />}
            </Button>
          </div>
        </div>
      </div>
      
      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-[#1a202c] border-t border-gray-800">
          <div className="container mx-auto px-4 py-4 space-y-2">
            <a href="#features" className="block text-gray-300 hover:text-white px-3 py-2 rounded-md text-base font-medium">
              Features
            </a>
            <a href="#how-it-works" className="block text-gray-300 hover:text-white px-3 py-2 rounded-md text-base font-medium">
              How It Works
            </a>
            <a href="#pricing" className="block text-gray-300 hover:text-white px-3 py-2 rounded-md text-base font-medium">
              Pricing
            </a>
            <a href="#testimonials" className="block text-gray-300 hover:text-white px-3 py-2 rounded-md text-base font-medium">
              Testimonials
            </a>
            <div className="pt-4 space-y-2">
              <Button 
                variant="ghost"
                className="text-gray-300 hover:text-white border-none w-full"
                onClick={() => window.location.href = '/login'}
              >
                Log in
              </Button>
              <Button 
                className="bg-blue-600 hover:bg-blue-700 text-white w-full"
                onClick={() => window.location.href = '/dashboard'}
              >
                Sign up
              </Button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default NavBar;
