import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../services/api';

const TicketDetail = () => {
  const { id } = useParams();
  const [ticket, setTicket] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [response, setResponse] = useState('');

  useEffect(() => {
    api.get(`/tickets/${id}/`).then(res => {
      setTicket(res.data.ticket);
      setAnalysis(res.data.analysis);
      setResponse(res.data.analysis?.ai_response || '');
    }).catch(err => console.error(err));
  }, [id]);

  const updateResponse = () => {
    api.put(`/analysis/${analysis.id}/update/`, { ai_response: response })
       .then(() => alert('Réponse mise à jour'));
  };

  const validateResponse = () => {
    api.post(`/analysis/${analysis.id}/validate/`)
       .then(() => alert('Réponse validée'));
  };

  const sendToZammad = () => {
    api.post(`/analysis/${analysis.id}/send/`)
       .then(() => alert('Envoyé vers Zammad'));
  };

  if (!ticket) return <div>Chargement...</div>;

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-2xl mb-4">{ticket.title || 'Titre non disponible'}</h1>
      <div className="mb-6 p-4 bg-gray-100 rounded">
        <p><strong>Client:</strong> {ticket.customer_email || 'Email non disponible'}</p>
        <p><strong>Statut:</strong> {ticket.status || 'Statut non disponible'}</p>
        <p><strong>Contenu:</strong> {ticket.body || 'Contenu non disponible'}</p>
        <p><strong>Créé le:</strong> {ticket.created_at ? new Date(ticket.created_at).toLocaleString() : 'Date non disponible'}</p>
      </div>
      
      {analysis ? (
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 rounded">
            <h3 className="font-bold">Réponse IA</h3>
            <p>{analysis.ai_response}</p>
          </div>
          
          <textarea 
            value={response} 
            onChange={(e) => setResponse(e.target.value)}
            className="w-full h-32 p-3 border rounded"
            placeholder="Modifier la réponse..."
          />
          
          <div className="flex gap-2">
            <button onClick={updateResponse} 
                    className="px-4 py-2 bg-blue-500 text-white rounded">
              Sauvegarder
            </button>
            <button onClick={validateResponse} 
                    className="px-4 py-2 bg-green-500 text-white rounded">
              Valider
            </button>
            <button onClick={sendToZammad} 
                    className="px-4 py-2 bg-purple-500 text-white rounded">
              Envoyer Zammad
            </button>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-yellow-50 rounded">
          <p>Aucune analyse IA disponible pour ce ticket.</p>
        </div>
      )}
    </div>
  );
};

export default TicketDetail;
