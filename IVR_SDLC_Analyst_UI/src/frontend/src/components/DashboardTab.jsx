export async function flowAudit() {

    const response =
      await fetch(
         "http://localhost:8000/api/analyze/flow",
         {
             method: "POST"
         }
      );

    return await response.json();
}