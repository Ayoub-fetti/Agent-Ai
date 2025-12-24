import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import api from "../../services/api";

const TicketDetail = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get(`/tickets/${id}/`).then((res) => setData(res.data));
  }, [id]);

  const analyzeTicket = async () => {
    setLoading(true);
    try {
      const response = await api.post(`/tickets/${id}/analyze/`);
      setAnalysis(response.data.analysis);
    } catch {
      alert("Erreur lors de l'analyse");
    }
    setLoading(false);
  };

  if (!data) return <div>Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl mb-4">{data.ticket.title}</h1>

      <button
        onClick={analyzeTicket}
        disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded mb-4"
      >
        {loading ? "Analyse en cours..." : "Analyser avec IA"}
      </button>

      {analysis && (
        <div className="bg-gray-100 p-4 rounded mb-4">
          <h3 className="font-bold mb-2">Analyse IA:</h3>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <strong>Intention:</strong> {analysis.intention}
            </div>
            <div>
              <strong>Catégorie:</strong> {analysis.category}
            </div>
            <div>
              <strong>Priorité:</strong> {analysis.priority}
            </div>
          </div>
          <div className="mt-4">
            <strong>Réponse suggérée:</strong>
            <div
              className="bg-white p-4 rounded mt-2 prose max-w-none"
              dangerouslySetInnerHTML={{ __html: analysis.ai_response }}
            />
          </div>
        </div>
      )}

      <div className="mb-6">
        <p>
          <strong>Number:</strong> {data.ticket.number}
        </p>
        <p>
          <strong>State:</strong> {data.ticket.state_id}
        </p>
      </div>

      <h2 className="text-xl mb-4">Messages:</h2>
      {data.articles.map((article) => (
        <div key={article.id} className="border p-4 mb-4 rounded">
          <div className="mb-2 text-sm text-gray-600">
            {new Date(article.created_at).toLocaleString()}
          </div>
          <div dangerouslySetInnerHTML={{ __html: article.body }} />
        </div>
      ))}
    </div>
  );
};

export default TicketDetail;
