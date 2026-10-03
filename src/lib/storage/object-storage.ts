import { createHmac, createHash } from "crypto";

const defaultExpiresSeconds = 60 * 10;

export type ObjectStorageConfig = {
  provider: string;
  endpoint: string;
  bucket: string;
  region: string;
  accessKeyId: string;
  secretAccessKey: string;
  publicBaseUrl?: string;
};

export type PresignedUpload = {
  provider: string;
  bucket: string;
  path: string;
  url: string;
  publicUrl?: string;
  expiresAt: string;
};

function requiredEnv(name: string) {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

export function hasObjectStorageConfig() {
  return Boolean(
    process.env.OBJECT_STORAGE_ENDPOINT &&
      process.env.OBJECT_STORAGE_BUCKET &&
      process.env.OBJECT_STORAGE_ACCESS_KEY_ID &&
      process.env.OBJECT_STORAGE_SECRET_ACCESS_KEY,
  );
}

export function getObjectStorageConfig(): ObjectStorageConfig {
  return {
    provider: process.env.OBJECT_STORAGE_PROVIDER?.trim() || "s3",
    endpoint: requiredEnv("OBJECT_STORAGE_ENDPOINT").replace(/\/+$/, ""),
    bucket: requiredEnv("OBJECT_STORAGE_BUCKET"),
    region: process.env.OBJECT_STORAGE_REGION?.trim() || "auto",
    accessKeyId: requiredEnv("OBJECT_STORAGE_ACCESS_KEY_ID"),
    secretAccessKey: requiredEnv("OBJECT_STORAGE_SECRET_ACCESS_KEY"),
    publicBaseUrl: process.env.OBJECT_STORAGE_PUBLIC_BASE_URL?.trim().replace(/\/+$/, "") || undefined,
  };
}

function hmac(key: Buffer | string, value: string) {
  return createHmac("sha256", key).update(value, "utf8").digest();
}

function sha256(value: string) {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function getSigningKey(secretAccessKey: string, dateStamp: string, region: string, service: string) {
  const dateKey = hmac(`AWS4${secretAccessKey}`, dateStamp);
  const regionKey = hmac(dateKey, region);
  const serviceKey = hmac(regionKey, service);
  return hmac(serviceKey, "aws4_request");
}

function amzDate(now: Date) {
  return now.toISOString().replace(/[:-]|\.\d{3}/g, "");
}

function encodePath(path: string) {
  return path
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

function encodeQuery(value: string) {
  return encodeURIComponent(value).replace(/[!'()*]/g, (char) => `%${char.charCodeAt(0).toString(16).toUpperCase()}`);
}

export function createPresignedPutUrl(path: string, expiresSeconds = defaultExpiresSeconds): PresignedUpload {
  const config = getObjectStorageConfig();
  const endpoint = new URL(config.endpoint);
  const now = new Date();
  const dateTime = amzDate(now);
  const dateStamp = dateTime.slice(0, 8);
  const service = "s3";
  const scope = `${dateStamp}/${config.region}/${service}/aws4_request`;
  const credential = `${config.accessKeyId}/${scope}`;
  const canonicalUri = `/${encodePath(config.bucket)}/${encodePath(path)}`;
  const host = endpoint.host;

  const queryParams: Record<string, string> = {
    "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
    "X-Amz-Credential": credential,
    "X-Amz-Date": dateTime,
    "X-Amz-Expires": String(expiresSeconds),
    "X-Amz-SignedHeaders": "host",
  };

  const canonicalQueryString = Object.entries(queryParams)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${encodeQuery(key)}=${encodeQuery(value)}`)
    .join("&");

  const canonicalRequest = [
    "PUT",
    canonicalUri,
    canonicalQueryString,
    `host:${host}`,
    "",
    "host",
    "UNSIGNED-PAYLOAD",
  ].join("\n");

  const stringToSign = [
    "AWS4-HMAC-SHA256",
    dateTime,
    scope,
    sha256(canonicalRequest),
  ].join("\n");

  const signingKey = getSigningKey(config.secretAccessKey, dateStamp, config.region, service);
  const signature = createHmac("sha256", signingKey).update(stringToSign, "utf8").digest("hex");
  const url = `${endpoint.origin}${canonicalUri}?${canonicalQueryString}&X-Amz-Signature=${signature}`;
  const publicUrl = config.publicBaseUrl ? `${config.publicBaseUrl}/${encodePath(path)}` : undefined;

  return {
    provider: config.provider,
    bucket: config.bucket,
    path,
    url,
    publicUrl,
    expiresAt: new Date(now.getTime() + expiresSeconds * 1000).toISOString(),
  };
}

