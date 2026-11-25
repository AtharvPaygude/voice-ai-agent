/**
 * DiscoveryPanel.tsx — Real Provider Discovery for Customers
 *
 * Queries the real backend discovery API (/api/discovery/search) and shows
 * live registered businesses with their available slots.
 * Supports category filter chips (Doctor, Hotel, Restaurant) + text search.
 *
 * Only shows real published providers from the DB — no fake data.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { API_BASE_URL as API } from '../../utils/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ProviderResult {
  id: string;
  name: string;
  category: string;
  industry: string;
  description: string;
  address: string;
  city: string;
  booking_unit_label: string;
  specialties: string[];
  practitioners: Array<{ name: string; specialty: string; fee?: string }>;
  offerings: Array<{ name: string; price?: string }>;
  sample_available_slots: string[];
  earliest_available_date: string | null;
}

// ─── Category definitions ──────────────────────────────────────────────────────

const CATEGORIES = [
  { key: '', label: 'All', icon: 'apps' },
  { key: 'clinic_doctor', label: 'Doctor / Clinic', icon: 'local_hospital' },
  { key: 'hotel', label: 'Hotel', icon: 'hotel' },
  { key: 'restaurant', label: 'Restaurant', icon: 'restaurant' },
  { key: 'service_business', label: 'Services', icon: 'handyman' },
];

const CATEGORY_ACCENT: Record<string, string> = {
  clinic_doctor: '#65f2b5',
  hotel: '#fbbf24',
  restaurant: '#f87171',
  service_business: '#00f0ff',
  '': '#d0bcff',
};

// ─── Component ────────────────────────────────────────────────────────────────

export const DiscoveryPanel: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [providers, setProviders] = useState<ProviderResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalFound, setTotalFound] = useState(0);
  const [selectedProvider, setSelectedProvider] = useState<ProviderResult | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [bookingDate, setBookingDate] = useState<string>('');
  const [bookingStatus, setBookingStatus] = useState<string | null>(null);
  const [bookingLoading, setBookingLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Default booking date: tomorrow
  useEffect(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setBookingDate(tomorrow.toISOString().split('T')[0]);
  }, []);

  const fetchProviders = useCallback(async (cat: string, q: string) => {
    setLoading(true);
    setBookingStatus(null);
    try {
      const params = new URLSearchParams();
      if (cat) params.set('category', cat);
      if (q) params.set('q', q);
      const res = await fetch(`${API}/api/discovery/search?${params.toString()}`);
      if (!res.ok) throw new Error('Discovery search failed');
      const data = await res.json();
      setProviders(data.providers || []);
      setTotalFound(data.total_found || 0);
    } catch {
      setProviders([]);
      setTotalFound(0);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load + category-triggered load
  useEffect(() => {
    fetchProviders(selectedCategory, searchQuery);
  }, [selectedCategory]); // eslint-disable-line

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchProviders(selectedCategory, searchQuery);
    }, 400);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [searchQuery]); // eslint-disable-line

  const handleBook = useCallback(async () => {
    if (!selectedProvider || !selectedSlot || !bookingDate) return;
    setBookingLoading(true);
    setBookingStatus(null);
    try {
      const res = await fetch(`${API}/api/tools/book_slot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: selectedProvider.id,
          date: bookingDate,
          time: selectedSlot,
          customer_name: 'Walk-in Customer',
          service_type: selectedProvider.offerings[0]?.name || selectedProvider.booking_unit_label,
        }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setBookingStatus(`✅ Booked! ${selectedProvider.name} on ${bookingDate} at ${selectedSlot}`);
        setSelectedSlot(null);
        // Refresh slots
        await fetchProviders(selectedCategory, searchQuery);
      } else {
        setBookingStatus(`❌ ${data.message || 'Booking failed. Slot may be taken.'}`);
      }
    } catch {
      setBookingStatus('❌ Network error. Please try again.');
    } finally {
      setBookingLoading(false);
    }
  }, [selectedProvider, selectedSlot, bookingDate, selectedCategory, searchQuery, fetchProviders]);

  return (
    <div className="glass-panel rounded-xl p-5 gradient-border-top flex flex-col gap-4 min-h-[300px]">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-[#00f0ff]">Provider Discovery</p>
          <p className="text-[11px] text-[#b9cacb] font-mono mt-0.5">Real registered businesses</p>
        </div>
        <div className="flex items-center gap-1">
          {loading && <div className="w-3.5 h-3.5 border border-[#00f0ff] border-t-transparent rounded-full animate-spin" />}
          {!loading && totalFound > 0 && (
            <span className="text-[10px] font-mono text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/20 px-2 py-0.5 rounded">
              {totalFound} found
            </span>
          )}
        </div>
      </div>

      {/* Category Chips */}
      <div className="flex flex-wrap gap-1.5">
        {CATEGORIES.map((cat) => {
          const isActive = selectedCategory === cat.key;
          const chipAccent = CATEGORY_ACCENT[cat.key] || '#d0bcff';
          return (
            <button
              key={cat.key}
              onClick={() => {
                setSelectedCategory(cat.key);
                setSelectedProvider(null);
                setSelectedSlot(null);
              }}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-mono font-semibold uppercase transition-all cursor-pointer border ${
                isActive
                  ? 'text-[#080e1d] border-transparent shadow-[0_0_10px_rgba(0,240,255,0.3)]'
                  : 'bg-transparent border-white/10 text-[#b9cacb] hover:border-white/25 hover:text-[#dde2f8]'
              }`}
              style={isActive ? { backgroundColor: chipAccent, borderColor: chipAccent } : {}}
            >
              <span className="material-symbols-outlined text-[12px]">{cat.icon}</span>
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Search bar */}
      <div className="relative">
        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[16px] text-[#849495]">search</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search doctors, specialties, hotels..."
          className="w-full pl-8 pr-4 py-2 bg-[#080e1d] border border-white/10 rounded-lg text-xs font-mono text-[#dde2f8] placeholder-[#849495] focus:outline-none focus:border-[#00f0ff] transition-colors"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#849495] hover:text-[#dde2f8] cursor-pointer"
          >
            <span className="material-symbols-outlined text-[14px]">close</span>
          </button>
        )}
      </div>

      {/* Provider List */}
      {loading && providers.length === 0 ? (
        <div className="flex items-center justify-center py-8 gap-2">
          <div className="w-4 h-4 border border-[#00f0ff] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-mono text-[#b9cacb]">Searching providers...</span>
        </div>
      ) : providers.length === 0 ? (
        <div className="text-center py-8">
          <span className="material-symbols-outlined text-[36px] text-[#2f3445] mb-2 block">search_off</span>
          <p className="text-xs text-[#b9cacb] font-mono">No registered providers found.</p>
          <p className="text-[10px] text-[#849495] mt-1">Register your business at /onboarding to appear here.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3 max-h-[380px] overflow-y-auto pr-1 custom-scrollbar">
          {providers.map((provider) => {
            const pAccent = CATEGORY_ACCENT[provider.category] || '#d0bcff';
            const isSelected = selectedProvider?.id === provider.id;
            return (
              <div
                key={provider.id}
                onClick={() => {
                  setSelectedProvider(isSelected ? null : provider);
                  setSelectedSlot(null);
                  setBookingStatus(null);
                }}
                className={`rounded-xl border p-4 cursor-pointer transition-all ${
                  isSelected
                    ? 'border-[#00f0ff]/50 bg-[#00f0ff]/5 shadow-[0_0_15px_rgba(0,240,255,0.1)]'
                    : 'border-white/8 bg-[#191f2f]/40 hover:border-white/20 hover:bg-[#191f2f]/60'
                }`}
              >
                {/* Provider header */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-['Sora'] font-semibold text-sm text-[#dde2f8] truncate">{provider.name}</h4>
                      <span
                        className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border shrink-0"
                        style={{ color: pAccent, borderColor: `${pAccent}40`, backgroundColor: `${pAccent}15` }}
                      >
                        {provider.industry}
                      </span>
                    </div>
                    {provider.city && (
                      <p className="text-[10px] text-[#849495] font-mono flex items-center gap-1 mt-0.5">
                        <span className="material-symbols-outlined text-[11px]">location_on</span>
                        {provider.city}
                      </p>
                    )}
                  </div>
                  <div className="shrink-0">
                    {provider.earliest_available_date ? (
                      <span className="text-[9px] font-mono text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/20 px-1.5 py-0.5 rounded">
                        AVAIL
                      </span>
                    ) : (
                      <span className="text-[9px] font-mono text-[#849495] bg-white/5 border border-white/10 px-1.5 py-0.5 rounded">
                        NO SLOTS
                      </span>
                    )}
                  </div>
                </div>

                {/* Specialties / Offerings */}
                {provider.specialties.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {provider.specialties.slice(0, 3).map((s) => (
                      <span key={s} className="text-[9px] font-mono text-[#b9cacb] bg-[#191f2f] border border-white/8 px-1.5 py-0.5 rounded">
                        {s}
                      </span>
                    ))}
                  </div>
                )}

                {/* Sample slots preview */}
                {provider.sample_available_slots.length > 0 && !isSelected && (
                  <div className="flex items-center gap-1.5 mt-2">
                    <span className="material-symbols-outlined text-[12px] text-[#00f0ff]">schedule</span>
                    <span className="text-[9px] font-mono text-[#849495]">Slots:</span>
                    {provider.sample_available_slots.slice(0, 3).map((s) => (
                      <span key={s} className="text-[9px] font-mono text-[#00f0ff] bg-[#00f0ff]/10 px-1.5 py-0.5 rounded border border-[#00f0ff]/20">
                        {s}
                      </span>
                    ))}
                    {provider.sample_available_slots.length > 3 && (
                      <span className="text-[9px] font-mono text-[#849495]">+{provider.sample_available_slots.length - 3}</span>
                    )}
                  </div>
                )}

                {/* Expanded booking panel */}
                {isSelected && (
                  <div
                    className="mt-3 pt-3 border-t border-white/8"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {/* Practitioners */}
                    {provider.practitioners.length > 0 && (
                      <div className="mb-3">
                        <p className="text-[9px] font-mono uppercase text-[#849495] mb-1.5">Practitioners</p>
                        {provider.practitioners.map((p, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs mb-1">
                            <span className="material-symbols-outlined text-[13px] text-[#d0bcff]">person</span>
                            <span className="text-[#dde2f8] font-mono text-[11px]">{p.name}</span>
                            {p.specialty && <span className="text-[#b9cacb] text-[10px]">· {p.specialty}</span>}
                            {p.fee && <span className="text-[#65f2b5] text-[10px] ml-auto">{p.fee}</span>}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Date picker */}
                    <div className="mb-3 flex items-center gap-2">
                      <span className="text-[9px] font-mono uppercase text-[#849495] shrink-0">Date:</span>
                      <input
                        type="date"
                        value={bookingDate}
                        min={new Date().toISOString().split('T')[0]}
                        onChange={(e) => setBookingDate(e.target.value)}
                        className="bg-[#080e1d] border border-white/15 rounded-lg px-2 py-1 text-[10px] font-mono text-[#dde2f8] focus:outline-none focus:border-[#00f0ff] transition-colors flex-1"
                      />
                    </div>

                    {/* Slot picker */}
                    {provider.sample_available_slots.length > 0 ? (
                      <div className="mb-3">
                        <p className="text-[9px] font-mono uppercase text-[#849495] mb-1.5">
                          Available Slots ({provider.earliest_available_date || bookingDate})
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {provider.sample_available_slots.map((slot) => {
                            const isSel = selectedSlot === slot;
                            return (
                              <button
                                key={slot}
                                onClick={() => setSelectedSlot(isSel ? null : slot)}
                                className={`px-2.5 py-1.5 rounded-lg text-[10px] font-mono font-semibold border transition-all cursor-pointer ${
                                  isSel
                                    ? 'bg-[#00f0ff] text-[#00363a] border-[#00f0ff] shadow-[0_0_10px_rgba(0,240,255,0.4)]'
                                    : 'bg-[#080e1d] border-white/15 text-[#b9cacb] hover:border-[#00f0ff]/50 hover:text-[#00f0ff]'
                                }`}
                              >
                                {slot}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    ) : (
                      <p className="text-[10px] font-mono text-[#849495] mb-3">No available slots for tomorrow. Try a different date.</p>
                    )}

                    {/* Book button */}
                    <button
                      onClick={handleBook}
                      disabled={!selectedSlot || bookingLoading}
                      className="w-full py-2 px-4 bg-gradient-to-r from-[#571bc1] to-[#00f0ff] text-[#080e1d] font-bold text-xs rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer disabled:opacity-50 shadow-[0_0_15px_rgba(0,240,255,0.2)] hover:brightness-110"
                    >
                      {bookingLoading ? (
                        <div className="w-3.5 h-3.5 border-2 border-[#080e1d]/50 border-t-[#080e1d] rounded-full animate-spin" />
                      ) : (
                        <span className="material-symbols-outlined text-[14px]">calendar_add_on</span>
                      )}
                      Book {selectedSlot ? `at ${selectedSlot}` : `${provider.booking_unit_label}`}
                    </button>

                    {/* Booking status */}
                    {bookingStatus && (
                      <div className={`mt-2 px-3 py-2 rounded-lg text-[10px] font-mono border ${
                        bookingStatus.startsWith('✅')
                          ? 'bg-[#65f2b5]/10 border-[#65f2b5]/30 text-[#65f2b5]'
                          : 'bg-[#93000a]/20 border-[#ffb4ab]/30 text-[#ffb4ab]'
                      }`}>
                        {bookingStatus}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DiscoveryPanel;
