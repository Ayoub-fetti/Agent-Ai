import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../../services/api";

const TicketDetail = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [creatingArticle, setCreatingArticle] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);

  useEffect(() => {
    setPageLoading(true);
    api
      .get(`/tickets/${id}/`)
      .then((res) => setData(res.data))
      .catch((err) => {
        console.error("Error fetching ticket:", err);
      })
      .finally(() => {
        setPageLoading(false);
      });
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

  const createInternalArticle = async () => {
    if (!analysis) return;

    setCreatingArticle(true);
    try {
      const articleBody = `
        <h3>Analyse IA du ticket</h3>
        <p><strong>Intention:</strong> ${analysis.intention}</p>
        <p><strong>Catégorie:</strong> ${analysis.category}</p>
        <p><strong>Priorité:</strong> ${analysis.priority}</p>
        
        <h4>Réponse proposée:</h4>
        <p>${analysis.ai_response.response}</p>
        
        <h4>Solution:</h4>
        <ul>
          ${analysis.ai_response.solution.map((step) => `<li>${step}</li>`).join("")}
        </ul>
      `;

      await api.post(`/tickets/${id}/internal-article/`, {
        subject: "Analyse IA - Note interne",
        body: articleBody,
      });

      alert("Article interne créé avec succès");
    } catch {
      alert("Erreur lors de la création de l'article");
    }
    setCreatingArticle(false);
  };

  const getStatusBadgeColor = (stateId) => {
    switch (stateId) {
      case 1:
        return "bg-green-100 text-green-800 border-green-200";
      case 2:
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case 3:
        return "bg-orange-100 text-orange-800 border-orange-200";
      case 4:
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusLabel = (stateId) => {
    switch (stateId) {
      case 1:
        return "En attente de cloture";
      case 2:
        return "Ouvert";
      case 3:
        return "Rappel en attente";
      case 4:
        return "En attente de Cloture";
      case 5:
        return "Clos";
      default:
        return stateId ? `Statut ${stateId}` : "Inconnu";
    }
  };

  const getPriorityBadgeColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case "urgent":
      case "urgente":
        return "bg-red-100 text-red-800 border-red-200";
      case "high":
      case "élevée":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "medium":
      case "moyenne":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
      case "faible":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getPriorityLabel = (priority) => {
    switch (priority?.toLowerCase()) {
      case "urgent":
        return "Urgente";
      case "high":
        return "Élevée";
      case "medium":
        return "Moyenne";
      case "low":
        return "Faible";
      default:
        return priority || "Non définie";
    }
  };

  if (pageLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-4xl text-blue-600 mb-4"></i>
          <p className="text-gray-600 text-lg">Chargement du ticket...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
          <p className="text-gray-600 text-lg">Ticket non trouvé</p>
          <Link
            to="/tickets"
            className="mt-4 inline-block text-blue-600 hover:text-blue-800"
          >
            Retour à la liste
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            to="/tickets"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-4 transition-colors"
          >
            <i className="fas fa-arrow-left"></i>
            <span>Retour à la liste</span>
          </Link>
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <i className="fas fa-ticket-alt text-2xl text-blue-600"></i>
                <h1 className="text-3xl font-bold text-gray-900">
                  {data.ticket.title || "Sans titre"}
                </h1>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <i className="fas fa-hashtag text-gray-400"></i>
                  <span className="font-mono">
                    #{data.ticket.number || data.ticket.id}
                  </span>
                </div>
                {data.ticket.state_id && (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusBadgeColor(
                      data.ticket.state_id
                    )}`}
                  >
                    {getStatusLabel(data.ticket.state_id)}
                  </span>
                )}
                {data.ticket.created_at && (
                  <div className="flex items-center gap-2">
                    <i className="fas fa-calendar text-gray-400"></i>
                    <span>
                      {new Date(data.ticket.created_at).toLocaleDateString("fr-FR", {
                        day: "numeric",
                        month: "long",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* AI Analysis Button */}
        <div className="mb-6">
          <button
            onClick={analyzeTicket}
            disabled={loading}
            className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 rounded-lg shadow-md hover:shadow-lg hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
          >
            {loading ? (
              <>
                <i className="fas fa-spinner fa-spin"></i>
                <span>Analyse en cours...</span>
              </>
            ) : (
              <>
                <i className="fas fa-robot"></i>
                <span>Analyser avec IA</span>
              </>
            )}
          </button>
        </div>

        {/* AI Analysis Results */}
        {analysis && (
          <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <i className="fas fa-brain text-blue-600 text-xl"></i>
              <h3 className="text-xl font-bold text-gray-900">Analyse IA</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
                <div className="flex items-center gap-2 mb-2">
                  <i className="fas fa-lightbulb text-blue-600"></i>
                  <span className="text-sm font-medium text-gray-600">Intention</span>
                </div>
                <p className="text-gray-900 font-semibold">{analysis.intention}</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-100">
                <div className="flex items-center gap-2 mb-2">
                  <i className="fas fa-tags text-purple-600"></i>
                  <span className="text-sm font-medium text-gray-600">Catégorie</span>
                </div>
                <p className="text-gray-900 font-semibold">{analysis.category}</p>
              </div>
              <div className="bg-orange-50 rounded-lg p-4 border border-orange-100">
                <div className="flex items-center gap-2 mb-2">
                  <i className="fas fa-exclamation-circle text-orange-600"></i>
                  <span className="text-sm font-medium text-gray-600">Priorité</span>
                </div>
                <span
                  className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${getPriorityBadgeColor(
                    analysis.priority
                  )}`}
                >
                  {getPriorityLabel(analysis.priority)}
                </span>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-5 mb-4 border-l-4 border-blue-500">
              <div className="flex items-center gap-2 mb-3">
                <i className="fas fa-comment-dots text-blue-600"></i>
                <h4 className="font-semibold text-blue-900 text-lg">
                  Réponse à votre demande
                </h4>
              </div>
              <p className="text-gray-800 leading-relaxed">{analysis.ai_response.response}</p>
            </div>

            <div className="bg-green-50 rounded-lg p-5 mb-4 border-l-4 border-green-500">
              <div className="flex items-center gap-2 mb-3">
                <i className="fas fa-check-circle text-green-600"></i>
                <h4 className="font-semibold text-green-900 text-lg">
                  Solution proposée
                </h4>
              </div>
              <ul className="space-y-2">
                {analysis.ai_response.solution.map((step, index) => (
                  <li key={index} className="flex items-start gap-2 text-gray-800">
                    <i className="fas fa-check text-green-600 mt-1"></i>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>

            <button
              onClick={createInternalArticle}
              disabled={creatingArticle}
              className="inline-flex items-center gap-2 bg-green-600 text-white px-5 py-2.5 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium shadow-sm"
            >
              {creatingArticle ? (
              <>
                <i className="fas fa-spinner fa-spin"></i>
                <span>Création...</span>
              </>
            ) : (
              <>
                <i className="fas fa-file-alt"></i>
                <span>Créer article interne</span>
              </>
            )}
            </button>
          </div>
        )}

        {/* Ticket Info */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <i className="fas fa-info-circle text-gray-600"></i>
            <h2 className="text-xl font-bold text-gray-900">Informations du ticket</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.ticket.number && (
              <div>
                <span className="text-sm font-medium text-gray-600">Numéro:</span>
                <p className="text-gray-900 font-mono">#{data.ticket.number}</p>
              </div>
            )}
            {data.ticket.state_id && (
              <div>
                <span className="text-sm font-medium text-gray-600">Statut:</span>
                <p className="text-gray-900">{getStatusLabel(data.ticket.state_id)}</p>
              </div>
            )}
            {data.ticket.customer_id && (
              <div>
                <span className="text-sm font-medium text-gray-600">Client ID:</span>
                <p className="text-gray-900">#{data.ticket.customer_id}</p>
              </div>
            )}
            {data.ticket.priority_id && (
              <div>
                <span className="text-sm font-medium text-gray-600">Priorité ID:</span>
                <p className="text-gray-900">#{data.ticket.priority_id}</p>
              </div>
            )}
            {data.ticket.updated_at && (
              <div>
                <span className="text-sm font-medium text-gray-600">Dernière mise à jour:</span>
                <p className="text-gray-900">
                  {new Date(data.ticket.updated_at).toLocaleDateString("fr-FR", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Messages/Articles */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <i className="fas fa-comments text-gray-600"></i>
            <h2 className="text-xl font-bold text-gray-900">
              Messages ({data.articles?.length || 0})
            </h2>
          </div>
          {data.articles && data.articles.length > 0 ? (
            <div className="space-y-4">
              {data.articles.map((article) => (
                <div
                  key={article.id}
                  className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow bg-gray-50"
                >
                  <div className="flex items-center gap-2 mb-3 text-sm text-gray-600">
                    <i className="fas fa-clock"></i>
                    <span>
                      {new Date(article.created_at).toLocaleDateString("fr-FR", {
                        day: "numeric",
                        month: "long",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                  <div
                    className="prose prose-sm max-w-none text-gray-800"
                    dangerouslySetInnerHTML={{ __html: article.body }}
                  />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <i className="fas fa-inbox text-3xl mb-2"></i>
              <p>Aucun message disponible</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TicketDetail;
