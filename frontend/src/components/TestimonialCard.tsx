import { Card, CardContent, CardFooter } from "./ui/card";
import { Quote as QuoteIcon } from "lucide-react";

interface TestimonialCardProps {
  quote: string;
  author: string;
  role: string;
  image?: string;
}

const TestimonialCard = ({ quote, author, role, image }: TestimonialCardProps) => {
  return (
    <Card className="border-none bg-gray-800/90 hover:shadow-xl transition-all duration-300 rounded-md overflow-hidden border border-gray-700">
      <CardContent className="pt-8">
        <QuoteIcon className="h-8 w-8 text-blue-500 mb-6 opacity-80" />
        <p className="text-gray-300 italic mb-8 leading-relaxed text-lg">{quote}</p>
      </CardContent>
      <CardFooter className="border-t border-gray-700 pt-6 pb-4 flex items-center gap-4">
        {image ? (
          <div className="h-12 w-12 rounded-full bg-gray-700 overflow-hidden shadow-md">
            <img src={image} alt={author} className="h-full w-full object-cover" />
          </div>
        ) : (
          <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 text-white flex items-center justify-center font-bold shadow-md">
            {author.charAt(0)}
          </div>
        )}
        <div>
          <p className="font-semibold text-white text-base">{author}</p>
          <p className="text-sm text-gray-400">{role}</p>
        </div>
      </CardFooter>
    </Card>
  );
};

export default TestimonialCard;
