import React, { useState } from 'react';
import { ChevronDown, Globe } from 'lucide-react';
import './LanguageSelector.css';

const LANGUAGES = [
  { code: 'en', name: 'English', native: 'English' },
  { code: 'zu', name: 'Zulu', native: 'isiZulu' },
  { code: 'xh', name: 'Xhosa', native: 'isiXhosa' },
  { code: 'af', name: 'Afrikaans', native: 'Afrikaans' },
  { code: 'st', name: 'Sotho', native: 'Sesotho' }
];

const LanguageSelector = ({ selectedLanguage, onLanguageChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const selectedLang = LANGUAGES.find(lang => lang.code === selectedLanguage) || LANGUAGES[0];

  const handleLanguageSelect = (languageCode) => {
    onLanguageChange(languageCode);
    setIsOpen(false);
  };

  return (
    <div className="language-selector">
      <button 
        className="language-trigger"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Globe size={16} />
        <span>{selectedLang.code.toUpperCase()}</span>
        <ChevronDown size={16} className={isOpen ? 'rotate-180' : ''} />
      </button>

      {isOpen && (
        <div className="language-dropdown">
          {LANGUAGES.map((language) => (
            <button
              key={language.code}
              className={`language-option ${selectedLanguage === language.code ? 'selected' : ''}`}
              onClick={() => handleLanguageSelect(language.code)}
            >
              <div className="language-info">
                <span className="language-name">{language.name}</span>
                <span className="language-native">{language.native}</span>
              </div>
              {selectedLanguage === language.code && (
                <div className="selected-indicator"></div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;