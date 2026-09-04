import React, { useState } from 'react';
import { BookOpen, Search, Layers } from 'lucide-react';

const STATUTES = [
  {
    title: 'Indian Contract Act 1872',
    abbreviation: 'ICA',
    sectionsIndexed: 266,
    year: '1872',
    categories: ['Unlawful Terms', 'Breach & Remedies', 'Restraint of Trade', 'Void Agreements', 'Penalty Clauses'],
    sections: [
      { num: 'S.10', title: 'What agreements are contracts', desc: 'All agreements are contracts if they are made by the free consent of parties competent to contract, for a lawful consideration.' },
      { num: 'S.23', title: 'What considerations and objects are lawful', desc: 'The consideration or object of an agreement is lawful, unless forbidden by law, defeats provisions of law, or is fraudulent.' },
      { num: 'S.27', title: 'Agreement in restraint of trade, void', desc: 'Every agreement by which any one is restrained from exercising a lawful profession, trade or business of any kind, is to that extent void.' },
      { num: 'S.28', title: 'Agreements in restraint of legal proceedings, void', desc: 'Every agreement which restricts any party from enforcing rights under contract in ordinary tribunals is void.' },
      { num: 'S.73', title: 'Compensation for loss or damage caused by breach', desc: 'When a contract has been broken, the party who suffers by such breach is entitled to receive compensation from the party who broke the contract.' },
      { num: 'S.74', title: 'Compensation for breach where penalty stipulated', desc: 'When a contract contains a penalty clause, the party complaining is entitled to reasonable compensation not exceeding the amount named.' },
    ],
  },
  {
    title: 'Indian Penal Code 1860',
    abbreviation: 'IPC',
    sectionsIndexed: 511,
    year: '1860',
    categories: ['Cheating', 'Criminal Breach', 'Fraud Signals', 'Misrepresentation', 'Forgery'],
    sections: [
      { num: 'S.405', title: 'Criminal Breach of Trust', desc: 'Whoever, being in any manner entrusted with property, dishonestly misappropriates or converts to his own use that property.' },
      { num: 'S.415', title: 'Cheating', desc: 'Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property.' },
      { num: 'S.420', title: 'Cheating and dishonestly inducing delivery of property', desc: 'Cheating and thereby dishonestly inducing delivery of valuable securities or property.' },
      { num: 'S.463', title: 'Forgery', desc: 'Whoever makes any false document or false electronic record with intent to cause damage or injury.' },
    ],
  },
  {
    title: 'Constitution of India 1950',
    abbreviation: 'CONST',
    sectionsIndexed: 361,
    year: '1950',
    categories: ['Fundamental Rights', 'Public Policy', 'Equality Before Law', 'Freedom of Trade', 'Due Process'],
    sections: [
      { num: 'Art.14', title: 'Equality before law', desc: 'The State shall not deny to any person equality before the law or the equal protection of the laws within the territory of India.' },
      { num: 'Art.19(1)(g)', title: 'Right to practice any profession, trade or business', desc: 'All citizens shall have the right to practice any profession, or to carry on any occupation, trade or business.' },
      { num: 'Art.21', title: 'Protection of life and personal liberty', desc: 'No person shall be deprived of his life or personal liberty except according to procedure established by law.' },
      { num: 'Art.300A', title: 'Persons not to be deprived of property save by authority of law', desc: 'No person shall be deprived of his property save by authority of law.' },
      { num: 'Art.301', title: 'Freedom of trade, commerce and intercourse', desc: 'Trade, commerce and intercourse throughout the territory of India shall be free subject to other constitutional provisions.' },
    ],
  },
];

export const LawLibraryPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAct, setSelectedAct] = useState<string>('ALL');

  const filteredStatutes = STATUTES.filter((s) => {
    if (selectedAct !== 'ALL' && s.abbreviation !== selectedAct) return false;
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div className="card" style={{ background: 'linear-gradient(135deg, #EEF2FF 0%, #FFFFFF 100%)', border: '1px solid #C7D2FE', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '0.35rem' }}>
          <div style={{ width: '38px', height: '38px', borderRadius: '8px', background: 'var(--accent)', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <BookOpen size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Indian Statutory Knowledge Base
            </h2>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
              1,138 indexed sections and articles embedded with InLegalBERT in your local Qdrant vector database.
            </p>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ position: 'relative', minWidth: '280px', flex: 1 }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search statutes, sections, keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
            style={{ paddingLeft: '2.25rem', width: '100%' }}
          />
        </div>

        <div className="filter-btn-group">
          <button
            className={`filter-btn ${selectedAct === 'ALL' ? 'active' : ''}`}
            onClick={() => setSelectedAct('ALL')}
          >
            All Acts
          </button>
          <button
            className={`filter-btn ${selectedAct === 'ICA' ? 'active' : ''}`}
            onClick={() => setSelectedAct('ICA')}
          >
            Contract Act 1872
          </button>
          <button
            className={`filter-btn ${selectedAct === 'IPC' ? 'active' : ''}`}
            onClick={() => setSelectedAct('IPC')}
          >
            IPC 1860
          </button>
          <button
            className={`filter-btn ${selectedAct === 'CONST' ? 'active' : ''}`}
            onClick={() => setSelectedAct('CONST')}
          >
            Constitution
          </button>
        </div>
      </div>

      {/* Statutes Display */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {filteredStatutes.map((statute) => {
          const matchingSections = statute.sections.filter((sec) => {
            if (!searchQuery.trim()) return true;
            const q = searchQuery.toLowerCase();
            return (
              sec.num.toLowerCase().includes(q) ||
              sec.title.toLowerCase().includes(q) ||
              sec.desc.toLowerCase().includes(q)
            );
          });

          return (
            <div key={statute.abbreviation} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <span className="pill pill-info" style={{ fontWeight: 800 }}>
                    {statute.abbreviation}
                  </span>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {statute.title}
                  </h3>
                </div>

                <span className="pill pill-neutral">
                  <Layers size={13} />
                  {statute.sectionsIndexed} Sections Indexed
                </span>
              </div>

              {/* Categories */}
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                {statute.categories.map((cat) => (
                  <span key={cat} className="pill pill-neutral" style={{ fontSize: '0.74rem' }}>
                    {cat}
                  </span>
                ))}
              </div>

              {/* Sections Grid */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                {matchingSections.map((sec) => (
                  <div key={sec.num} style={{ background: 'var(--bg-app)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '0.75rem 1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.82rem', color: 'var(--accent)' }}>
                        {sec.num}
                      </span>
                      <span style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--text-primary)' }}>
                        {sec.title}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                      {sec.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
