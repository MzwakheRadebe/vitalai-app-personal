import React, { useState } from 'react';
import { ChevronDown, Globe } from 'lucide-react';
import './LanguageSelector.css';

// List of supported languages with their codes, English names, and native names
const LANGUAGES = [
  { code: 'en', name: 'English', native: 'English' },
  { code: 'zu', name: 'Zulu', native: 'isiZulu' },
  { code: 'xh', name: 'Xhosa', native: 'isiXhosa' },
  { code: 'st', name: 'Southern Sotho', native: 'Sesotho' },
  { code: 'tn', name: 'Tswana', native: 'Setswana' },
  { code: 'nso', name: 'Northern Sotho', native: 'Sepedi' },
  { code: 'ss', name: 'Swati', native: 'siSwati' },
  { code: 've', name: 'Venda', native: 'Tshivenda' },
  { code: 'ts', name: 'Tsonga', native: 'Xitsonga' },
  { code: 'nr', name: 'Southern Ndebele', native: 'isiNdebele' },
  { code: 'af', name: 'Afrikaans', native: 'Afrikaans' },
  { code: 'sasl', name: 'South African Sign Language', native: 'SASL' }
];

// LanguageSelector component allows users to select a language from a dropdown
const LanguageSelector = ({ selectedLanguage, onLanguageChange }) => {
  // State to control whether the dropdown is open or closed
  const [isOpen, setIsOpen] = useState(false);

  // Find the currently selected language object, default to the first language if not found
  const selectedLang = LANGUAGES.find(lang => lang.code === selectedLanguage) || LANGUAGES[0];

  // Handle language selection: call parent callback and close dropdown
  const handleLanguageSelect = (languageCode) => {
    onLanguageChange(languageCode);
    setIsOpen(false);
  };

  return (
    <div className="language-selector">
      {/* Button to trigger dropdown open/close */}
      <button 
        className="language-trigger"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Globe size={16} /> {/* Globe icon */}
        <span>{selectedLang.code.toUpperCase()}</span> {/* Current language code */}
        <ChevronDown size={16} className={isOpen ? 'rotate-180' : ''} /> {/* Dropdown arrow */}
      </button>

      {/* Dropdown menu with language options */}
      {isOpen && (
        <div className="language-dropdown">
          {LANGUAGES.map((language) => (
            <button
              key={language.code}
              className={`language-option ${selectedLanguage === language.code ? 'selected' : ''}`}
              onClick={() => handleLanguageSelect(language.code)}
            >
              <div className="language-info">
                <span className="language-name">{language.name}</span> {/* English name */}
                <span className="language-native">{language.native}</span> {/* Native name */}
              </div>
              {/* Indicator for selected language */}
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