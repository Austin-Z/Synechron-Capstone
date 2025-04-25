import { Separator } from "./ui/separator";
import { Facebook, Twitter, Instagram, Linkedin } from "lucide-react";

const Footer = () => {
  return (
    <footer className="bg-slate-900 text-slate-300 py-16">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-white font-bold text-lg mb-4">Fund of Funds Explorer</h3>
            <p className="text-slate-400 mb-4">A comprehensive platform for analyzing fund-of-funds investments with advanced data visualization and AI-powered insights.</p>
            <div className="flex space-x-4">
              <button className="text-slate-400 hover:text-white">
                <span className="sr-only">Facebook</span>
                <Facebook size={20} />
              </button>
              <button className="text-slate-400 hover:text-white">
                <span className="sr-only">Twitter</span>
                <Twitter size={20} />
              </button>
              <button className="text-slate-400 hover:text-white">
                <span className="sr-only">Instagram</span>
                <Instagram size={20} />
              </button>
              <button className="text-slate-400 hover:text-white">
                <span className="sr-only">LinkedIn</span>
                <Linkedin size={20} />
              </button>
            </div>
          </div>
          
          <div>
            <h3 className="text-white font-bold mb-4">Platform</h3>
            <ul className="space-y-2">
              <li><a href="#features" className="text-slate-400 hover:text-white">Features</a></li>
              <li><a href="/dashboard" className="text-slate-400 hover:text-white">Dashboard</a></li>
              <li><button className="text-slate-400 hover:text-white">Security</button></li>
              <li><button className="text-slate-400 hover:text-white">Roadmap</button></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-white font-bold mb-4">Resources</h3>
            <ul className="space-y-2">
              <li><button className="text-slate-400 hover:text-white">Documentation</button></li>
              <li><button className="text-slate-400 hover:text-white">API</button></li>
              <li><button className="text-slate-400 hover:text-white">Guides</button></li>
              <li><button className="text-slate-400 hover:text-white">Community</button></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-white font-bold mb-4">Contact</h3>
            <ul className="space-y-2">
              <li><button className="text-slate-400 hover:text-white">About</button></li>
              <li><button className="text-slate-400 hover:text-white">Blog</button></li>
              <li><a href="mailto:contact@fofexplorer.com" className="text-slate-400 hover:text-white">Email Us</a></li>
              <li><button className="text-slate-400 hover:text-white">Support</button></li>
            </ul>
          </div>
        </div>
        
        <Separator className="my-8 bg-slate-800" />
        
        <div className="flex flex-col md:flex-row justify-between items-center">
          <p className="text-slate-500 text-sm">
            &copy; {new Date().getFullYear()} Fund of Funds Explorer. All rights reserved.
          </p>
          <div className="flex space-x-4 mt-4 md:mt-0">
            <button className="text-slate-500 text-sm hover:text-slate-300">Privacy Policy</button>
            <button className="text-slate-500 text-sm hover:text-slate-300">Terms of Service</button>
            <button className="text-slate-500 text-sm hover:text-slate-300">Cookies</button>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
