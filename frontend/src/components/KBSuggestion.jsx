// Nouveau composant: src/components/KBSuggestion.jsx
import { useState } from 'react';
import { suggestKBArticle, createKBArticle } from '../services/api';
import { notify } from '../services/notifications';


const KBSuggestion = ({ ticketId, analysis }) => {
  const [suggestion, setSuggestion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  const getSuggestion = async () => {
    setLoading(true);
    try {
      const response = await suggestKBArticle(ticketId);
      setSuggestion(response.data.suggestion);
      notify.info("Suggestion générée avec succès");

    } catch (error) {
      console.error('Erreur suggestion KB:', error);
      notify.error("Erreur lors de la génération de la suggestion");

    }
    setLoading(false);
  };

  const createArticle = async () => {
    setCreating(true);
    try {
      const response = await createKBArticle({
        title: suggestion.title,
        content: suggestion.content,
        category: suggestion.category
      });
      if (response.data.success) {
        notify.success(`Article créé avec succès ! ID: ${response.data.article_id}`);
        setSuggestion(null);
      } else {
        notify.error(response.data.error || "Erreur lors de la création");
      }
    } catch (error) {
      notify.error('Erreur lors de la création de l\'article');
      console.error("Error creating article:", error);

    }
    setCreating(false);
  };

  if (!analysis || analysis.category !== 'technique') return null;

  return (
    <div className="bg-purple-50 rounded-lg p-4 border border-purple-200 mt-4">
      <div className="flex items-center gap-2 mb-3">
        <i className="fas fa-book text-purple-600"></i>
        <h4 className="font-semibold text-purple-900">Base de Connaissance</h4>
      </div>
      
      {!suggestion ? (
        <button
          onClick={getSuggestion}
          disabled={loading}
          className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? 'Analyse...' : 'Suggérer un article KB'}
        </button>
      ) : (
        <div>
          {suggestion.should_create ? (
            <div>
              <p className="text-green-700 mb-2">✓ {suggestion.reason}</p>
              <div className="bg-white p-3 rounded border mb-3">
                <h5 className="font-medium mb-1">{suggestion.title}</h5>
                <p className="text-sm text-gray-600">Catégorie: {suggestion.category}</p>
              </div>
              <button
                onClick={createArticle}
                disabled={creating}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
              >
                {creating ? 'Création...' : 'Créer l\'article'}
              </button>
            </div>
          ) : (
            <p className="text-gray-600">✗ {suggestion.reason}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default KBSuggestion;
