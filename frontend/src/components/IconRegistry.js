/* eslint-disable react/prop-types */
import React from 'react';
import * as Iconoir from 'iconoir-react';
import * as Lucide from 'lucide-react';

// Wrapper component to unify styles (e.g. strokeWidth, size, scaling)
const wrapIcon = (IconComponent, defaultProps = {}) => {
  return React.forwardRef(({ className = '', size = 24, strokeWidth, ...props }, ref) => {
    // Determine the stroke width: default to 1.6 to match high-quality SaaS designs (like Linear and Vercel)
    const stroke = strokeWidth !== undefined ? strokeWidth : (defaultProps.strokeWidth || 1.6);
    
    // Iconoir components support 'width' and 'height' instead of 'size'
    return (
      <IconComponent
        ref={ref}
        width={size}
        height={size}
        strokeWidth={stroke}
        className={`inline-block ${className}`}
        {...props}
      />
    );
  });
};

// Hand-crafted official brand SVGs to ensure premium visual quality, rather than generic font-pack icons.
export const GitHub = React.forwardRef(({ className = '', size = 20, ...props }, ref) => (
  <svg
    ref={ref}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="0"
    className={`inline-block ${className}`}
    {...props}
  >
    <path
      fill="currentColor"
      d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z"
    />
  </svg>
));

export const LinkedIn = React.forwardRef(({ className = '', size = 20, ...props }, ref) => (
  <svg
    ref={ref}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="0"
    className={`inline-block ${className}`}
    {...props}
  >
    <path
      fill="currentColor"
      d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.779-1.75-1.75s.784-1.75 1.75-1.75 1.75.779 1.75 1.75-.784 1.75-1.75 1.75zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"
    />
  </svg>
));

export const X = React.forwardRef(({ className = '', size = 18, ...props }, ref) => (
  <svg
    ref={ref}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={`inline-block ${className}`}
    {...props}
  >
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
));

export const Facebook = React.forwardRef(({ className = '', size = 20, ...props }, ref) => (
  <svg
    ref={ref}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="0"
    className={`inline-block ${className}`}
    {...props}
  >
    <path
      fill="currentColor"
      d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
    />
  </svg>
));

// Map semantic icon names to Iconoir icons
export const Home = wrapIcon(Iconoir.HomeSimple);
export const Menu = wrapIcon(Iconoir.Menu);
export const Cancel = wrapIcon(Iconoir.Xmark);
export const Info = wrapIcon(Iconoir.InfoCircle);
export const Users = wrapIcon(Iconoir.Group);
export const ChatBubble = wrapIcon(Iconoir.ChatBubble);
export const ChatBubbleEmpty = wrapIcon(Iconoir.ChatBubbleEmpty);
export const LogIn = wrapIcon(Iconoir.LogIn);
export const UserPlus = wrapIcon(Iconoir.UserPlus);
export const LogOut = wrapIcon(Iconoir.LogOut);
export const User = wrapIcon(Iconoir.User);
export const Settings = wrapIcon(Iconoir.Settings);
export const ChevronDown = wrapIcon(Iconoir.NavArrowDown);
export const ChevronRight = wrapIcon(Iconoir.NavArrowRight);
export const ChevronLeft = wrapIcon(Iconoir.NavArrowLeft);
export const Sun = wrapIcon(Iconoir.SunLight);
export const Moon = wrapIcon(Iconoir.HalfMoon);
export const Mail = wrapIcon(Iconoir.Mail);
export const Heart = wrapIcon(Iconoir.Heart);
export const ArrowRight = wrapIcon(Iconoir.ArrowRight);
export const ArrowLeft = wrapIcon(Iconoir.ArrowLeft);
export const ArrowUp = wrapIcon(Iconoir.ArrowUp);
export const Zap = wrapIcon(Iconoir.Flash);
export const Sparkles = wrapIcon(Iconoir.Spark);
export const Search = wrapIcon(Iconoir.Search);
export const Filter = wrapIcon(Iconoir.Filter);
export const HelpCircle = wrapIcon(Lucide.HelpCircle);
export const Clock = wrapIcon(Iconoir.Clock);
export const Folder = wrapIcon(Iconoir.Folder);
export const File = wrapIcon(Iconoir.Page);
export const Plus = wrapIcon(Iconoir.Plus);
export const PlusCircle = wrapIcon(Iconoir.PlusCircle);
export const Tag = wrapIcon(Iconoir.Label);
export const Trash = wrapIcon(Iconoir.Trash);
export const Lock = wrapIcon(Iconoir.Lock);
export const UserCheck = wrapIcon(Iconoir.UserBadgeCheck);
export const Eye = wrapIcon(Iconoir.Eye);
export const EyeClosed = wrapIcon(Iconoir.EyeClosed);
export const Camera = wrapIcon(Iconoir.Camera);
export const Save = wrapIcon(Iconoir.FloppyDisk);
export const Globe = wrapIcon(Iconoir.Globe);
export const Building = wrapIcon(Iconoir.Building);
export const Calendar = wrapIcon(Iconoir.Calendar);
export const Shield = wrapIcon(Iconoir.Shield);
export const Database = wrapIcon(Lucide.Database);
export const Activity = wrapIcon(Lucide.Activity);
export const Cpu = wrapIcon(Lucide.Cpu);
export const PenTool = wrapIcon(Lucide.PenTool);
export const Grid = wrapIcon(Lucide.Grid);
export const ViewGrid = wrapIcon(Lucide.LayoutGrid);
export const Sliders = wrapIcon(Lucide.SlidersHorizontal);
export const CheckSquare = wrapIcon(Lucide.CheckSquare);
export const Layers = wrapIcon(Lucide.Layers);
export const Download = wrapIcon(Iconoir.Download);
export const Upload = wrapIcon(Iconoir.Upload);
export const MousePointer = wrapIcon(Lucide.MousePointer);
export const BarChart = wrapIcon(Lucide.BarChart3);
export const Calculator = wrapIcon(Lucide.Calculator);
export const GitBranch = wrapIcon(Lucide.GitBranch);
export const Target = wrapIcon(Lucide.Target);
export const Compass = wrapIcon(Lucide.Compass);
export const Code = wrapIcon(Lucide.Code2);
export const Book = wrapIcon(Iconoir.Book);

// Fallbacks using Lucide for specific complex geometry/engineering symbols that Iconoir lacks or has weak design for.
export const Brain = wrapIcon(Lucide.Brain, { strokeWidth: 1.5 });
export const CheckCircle = wrapIcon(Lucide.CheckCircle2, { strokeWidth: 1.6 });
export const CheckCircle2 = wrapIcon(Lucide.CheckCircle2, { strokeWidth: 1.6 });
export const AlertTriangle = wrapIcon(Lucide.AlertTriangle, { strokeWidth: 1.6 });
export const SlidersHorizontal = wrapIcon(Lucide.SlidersHorizontal, { strokeWidth: 1.6 });
export const BookOpenCheck = wrapIcon(Lucide.BookOpenCheck, { strokeWidth: 1.5 });
export const BookOpen = wrapIcon(Lucide.BookOpen, { strokeWidth: 1.5 });
export const HardDriveUpload = wrapIcon(Lucide.HardDriveUpload, { strokeWidth: 1.5 });
export const Construction = wrapIcon(Lucide.Construction, { strokeWidth: 1.5 });
export const AlertCircle = wrapIcon(Lucide.AlertCircle, { strokeWidth: 1.6 });
export const Twitter = X; // map Twitter to X
export const MessageSquare = ChatBubbleEmpty;
export const MessageCircle = ChatBubble;
export const FileText = File;
export const History = wrapIcon(Lucide.History);
export const Link = wrapIcon(Lucide.Link);
export const LayoutGrid = ViewGrid;
export const BarChart3 = BarChart;
export const Trash2 = Trash;
export const Edit3 = wrapIcon(Lucide.Edit3);
