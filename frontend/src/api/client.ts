import { Client } from "@langchain/langgraph-sdk";
import { LANGGRAPH_URL } from "@/config/env";

/** לקוח יחיד לשרת של LangGraph, משותף לכל הממשק. */
export const client = new Client({ apiUrl: LANGGRAPH_URL });
