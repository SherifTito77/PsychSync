/**
 * Custom Date Range Picker Component
 * Provides flexible date range selection with presets
 */

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  X,
  Check,
  TrendingUp
} from 'lucide-react';

interface DateRangePickerProps {
  onDateRangeChange: (startDate: string, endDate: string) => void;
  initialStartDate?: string;
  initialEndDate?: string;
}

const PRESET_RANGES = [
  { label: 'Last 7 Days', days: 7, value: '7d' },
  { label: 'Last 30 Days', days: 30, value: '30d' },
  { label: 'Last 90 Days', days: 90, value: '90d' },
  { label: 'Last 6 Months', days: 180, value: '6m' },
  { label: 'Last Year', days: 365, value: '1y' },
];

export const CustomDateRangePicker: React.FC<DateRangePickerProps> = ({
  onDateRangeChange,
  initialStartDate,
  initialEndDate
}) => {
  const [selectedPreset, setSelectedPreset] = useState<string | null>('30d');
  const [startDate, setStartDate] = useState<string>(
    initialStartDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState<string>(
    initialEndDate || new Date().toISOString().split('T')[0]
  );
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarMonth, setCalendarMonth] = useState(new Date());

  const handlePresetClick = (days: number, value: string) => {
    setSelectedPreset(value);
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);

    const startDateStr = start.toISOString().split('T')[0];
    const endDateStr = end.toISOString().split('T')[0];

    setStartDate(startDateStr);
    setEndDate(endDateStr);
    setCalendarMonth(start);

    onDateRangeChange(startDateStr, endDateStr);
  };

  const handleCustomDateChange = (date: string, isStart: boolean) => {
    setSelectedPreset(null);

    if (isStart) {
      setStartDate(date);
      if (date > endDate) {
        setEndDate(date);
      }
    } else {
      setEndDate(date);
      if (date < startDate) {
        setStartDate(date);
      }
    }
  };

  const handleApply = () => {
    onDateRangeChange(startDate, endDate);
    setShowCalendar(false);
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    return { daysInMonth, startingDayOfWeek, year, month };
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newMonth = new Date(calendarMonth);
    if (direction === 'prev') {
      newMonth.setMonth(newMonth.getMonth() - 1);
    } else {
      newMonth.setMonth(newMonth.getMonth() + 1);
    }
    setCalendarMonth(newMonth);
  };

  const isDateInRange = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    return dateStr >= startDate && dateStr <= endDate;
  };

  const isStartDate = (date: Date) => {
    return date.toISOString().split('T')[0] === startDate;
  };

  const isEndDate = (date: Date) => {
    return date.toISOString().split('T')[0] === endDate;
  };

  const renderCalendar = (forStartDate: boolean) => {
    const { daysInMonth, startingDayOfWeek, year, month } = getDaysInMonth(calendarMonth);
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'];

    const days = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(<div key={`empty-${i}`} className="h-8" />);
    }

    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateStr = date.toISOString().split('T')[0];
      const inRange = isDateInRange(date);
      const isStart = isStartDate(date);
      const isEnd = isEndDate(date);
      const isSelected = forStartDate ? isStart : isEnd;
      const isDisabled = forStartDate
        ? dateStr > endDate
        : dateStr < startDate;

      days.push(
        <button
          key={day}
          onClick={() => !isDisabled && handleCustomDateChange(dateStr, forStartDate)}
          disabled={isDisabled}
          className={`
            h-8 w-8 rounded-full text-sm font-medium
            ${isDisabled
              ? 'text-gray-300 cursor-not-allowed'
              : 'hover:bg-blue-50 cursor-pointer'
            }
            ${inRange && !isStart && !isEnd && 'bg-blue-50'}
            ${isSelected && 'bg-blue-600 text-white hover:bg-blue-700'}
            ${isStart && 'bg-green-500 text-white'}
            ${isEnd && 'bg-purple-500 text-white'}
            transition-colors
          `}
        >
          {day}
        </button>
      );
    }

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigateMonth('prev')}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <div className="font-semibold">
            {monthNames[month]} {year}
          </div>
          <button
            onClick={() => navigateMonth('next')}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
        <div className="grid grid-cols-7 gap-1 text-center">
          {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
            <div key={day} className="text-xs font-medium text-gray-500 py-1">
              {day}
            </div>
          ))}
          {days}
        </div>
      </div>
    );
  };

  const calculateDaysBetween = () => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <div className="space-y-4">
      {/* Preset Ranges */}
      <div className="flex flex-wrap gap-2">
        {PRESET_RANGES.map(preset => (
          <Badge
            key={preset.value}
            variant={selectedPreset === preset.value ? "default" : "outline"}
            className="cursor-pointer hover:bg-gray-100"
            onClick={() => handlePresetClick(preset.days, preset.value)}
          >
            {preset.label}
          </Badge>
        ))}
        <Badge
          variant={selectedPreset === null ? "default" : "outline"}
          className="cursor-pointer hover:bg-gray-100"
          onClick={() => {
            setSelectedPreset(null);
            setShowCalendar(!showCalendar);
          }}
        >
          <Calendar className="h-3 w-3 mr-1" />
          Custom
        </Badge>
      </div>

      {/* Custom Date Range Selector */}
      {showCalendar && (
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Start Date Calendar */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-green-500" />
                  <label className="text-sm font-medium">Start Date</label>
                </div>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => handleCustomDateChange(e.target.value, true)}
                  className="w-full px-3 py-2 border rounded text-sm"
                />
                {renderCalendar(true)}
              </div>

              {/* End Date Calendar */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-purple-500" />
                  <label className="text-sm font-medium">End Date</label>
                </div>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => handleCustomDateChange(e.target.value, false)}
                  className="w-full px-3 py-2 border rounded text-sm"
                />
                {renderCalendar(false)}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-gray-600">
                <TrendingUp className="h-4 w-4 inline mr-1" />
                {calculateDaysBetween()} days selected
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCalendar(false)}
                >
                  <X className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleApply}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Check className="h-4 w-4 mr-2" />
                  Apply Range
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Selected Range Display */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 mb-1">Selected Date Range</div>
              <div className="font-semibold text-gray-900">
                {new Date(startDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                {' '}-{' '}
                {new Date(endDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </div>
            </div>
            <Badge variant="secondary" className="text-lg px-3">
              {calculateDaysBetween()} days
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
