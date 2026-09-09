import { useState } from 'react';

export function useActiveTab<T extends string>(initialTab: T) {
  const [activeTab, setActiveTab] = useState<T>(initialTab);
  return { activeTab, setActiveTab };
}
