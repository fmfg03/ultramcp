// Simple supabase adapter stub
const getSupabaseClient = () => {
  return {
    from: (table) => ({
      select: () => ({ data: [], error: null }),
      insert: () => ({ data: [], error: null }),
      update: () => ({ data: [], error: null }),
      delete: () => ({ data: [], error: null })
    })
  };
};

module.exports = { getSupabaseClient };