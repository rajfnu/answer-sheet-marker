import { NavLink } from 'react-router-dom';
import { Upload, FileCheck, BarChart3 } from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  {
    to: '/upload-assessment',
    icon: Upload,
    label: 'Upload Assessment',
    description: 'Upload marking guide',
  },
  {
    to: '/mark-answers',
    icon: FileCheck,
    label: 'Mark Answers',
    description: 'Grade student submissions',
  },
  {
    to: '/reports',
    icon: BarChart3,
    label: 'Reports',
    description: 'View marking results',
  },
];

export default function Sidebar() {
  return (
    <aside className="w-64 border-r border-border bg-card p-4">
      <nav className="space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex items-start gap-3 rounded-lg px-4 py-3 transition-colors',
                  'hover:bg-accent hover:text-accent-foreground',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground'
                )
              }
            >
              <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="font-medium">{item.label}</div>
                <div className="text-xs opacity-80">{item.description}</div>
              </div>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
