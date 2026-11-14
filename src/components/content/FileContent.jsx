export default function FileContent({ fileUrl }) {
  return (
    <iframe
      src={fileUrl}
      title="file preview"
      style={{ width: '100%', height: '70vh', border: 'none' }}
    />
  )
}
