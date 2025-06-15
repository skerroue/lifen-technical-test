function fetchResults(query: string) {
  return fetch(`API_DOMAIN/search?q=${query}`);
}

function Phonebook() {
  const [query, setQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [results, setResults] = useState<any>(undefined);

  const onChange = (event) => {
    setQuery(event.target.value);
    setIsLoading(true);

    try {
      const res = await fetchResults(query);
      setResults(res);
      setIsLoading(false);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  }

  return (
    <div>
      <div>
        <input value={query} onChange={onChange} />
      </div>
      {
        isLoading ? 'loading ...' : ''
      }
      {
        error ? <span>Something went wrong: {error}</span> : ''
      }
      <ul>
        {
          results.map(result => {
            return (
              <li>{result.name}: {result.phoneNumber}</li>
            );
          })
        }
      </ul>
    </div>
  );
}
